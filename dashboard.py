import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
from src.infrastructure.persistence.postgres_repo import PostgresRepository
from src.config.settings import INITIAL_PAPER_BALANCE

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="AI Trader Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Dark Glassmorphism) ---
st.markdown("""
    <style>
        /* Main Background */
        .stApp {
            background-color: #0e1117;
        }
        
        /* Metric Cards */
        div[data-testid="stMetric"] {
            background-color: #1e2127;
            border: 1px solid #2e3137;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        div[data-testid="stMetricValue"] {
            color: #ffffff;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #e0e0e0;
            font-family: 'Inter', sans-serif;
        }
        
        /* Tables */
        .stDataFrame {
            border: 1px solid #2e3137;
            border-radius: 5px;
        }
        
        /* Custom "Profit" Text */
        .profit-text { color: #00fa9a; font-weight: bold; }
        .loss-text { color: #ff4b4b; font-weight: bold; }
        
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---


@st.cache_resource
def get_repo(v=1):
    return PostgresRepository()


repo = get_repo(v=3)  # Inc version to force reload

# Auth State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False


def login():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🔐 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            if repo.verify_user(username, password):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid credentials")


def logout():
    st.session_state["authenticated"] = False
    st.rerun()


if not st.session_state["authenticated"]:
    login()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ AI Trader Pro")
    st.markdown("---")
    st.metric("Bot Status", "Active", "Running")

    if st.button("🔄 Refresh Data"):
        st.rerun()
    if st.button("🚪 Logout"):
        logout()

# --- HELPER FUNCTIONS ---


def filter_trades(trades, days):
    cutoff = datetime.utcnow() - timedelta(days=days)
    filtered = []
    for t in trades:
        if t['closed_at']:
            try:
                # Handle potential different formats or ensure ISO
                closed_dt = datetime.fromisoformat(t['closed_at'])
                if closed_dt >= cutoff:
                    filtered.append(t)
            except:
                pass
    return filtered


def calculate_pnl(trades):
    return sum(t['pnl'] for t in trades if t['pnl'] is not None)

# --- MAIN DASHBOARD ---


# 1. Fetch Data
state_bal = repo.load_state_value("paper_balance", INITIAL_PAPER_BALANCE)
total_pnl = repo.load_state_value("total_pnl", 0.0)
active_trades = repo.load_trades()
closed_trades = repo.load_closed_trades()
equity_history = repo.load_equity_history()

# 2. Top Metrics (Performance Cards)
st.markdown("### 🚀 Account Overview")
col1, col2, col3, col4 = st.columns(4)

# Current Balance
col1.metric("Account Balance", f"${state_bal:,.2f}", f"${total_pnl:,.2f}")

# Weekly PnL
weekly_trades = filter_trades(closed_trades, 7)
weekly_pnl = calculate_pnl(weekly_trades)
col2.metric("This Week", f"${weekly_pnl:,.2f}", f"{len(weekly_trades)} Trades")

# Monthly PnL
monthly_trades = filter_trades(closed_trades, 30)
monthly_pnl = calculate_pnl(monthly_trades)
col3.metric("This Month", f"${monthly_pnl:,.2f}",
            f"{len(monthly_trades)} Trades")

# Win Rate (All Time)
wins = len([t for t in closed_trades if t['pnl'] > 0])
total_closed = len(closed_trades)
win_rate = (wins / total_closed * 100) if total_closed > 0 else 0.0
col4.metric("Win Rate", f"{win_rate:.1f}%", f"{total_closed} Total")

# 3. Charts Row
st.markdown("---")
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📈 Equity Curve")
    if equity_history:
        df_eq = pd.DataFrame(equity_history)
        # Gradient Area Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_eq['timestamp'],
            y=df_eq['equity'],
            fill='tozeroy',
            mode='lines',
            line=dict(color='#00fa9a', width=2),
            name='Equity'
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e0e0e0'),
            margin=dict(l=0, r=0, t=10, b=0),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Waiting for data...")

with c2:
    st.subheader("📊 Trade Distribution")
    if closed_trades:
        # Bar Chart of Win/Loss
        df_closed = pd.DataFrame(closed_trades)
        df_closed['Color'] = df_closed['pnl'].apply(
            lambda x: '#00fa9a' if x >= 0 else '#ff4b4b')
        fig2 = go.Figure(go.Bar(
            x=df_closed['symbol'],
            y=df_closed['pnl'],
            marker_color=df_closed['Color']
        ))
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e0e0e0'),
            margin=dict(l=0, r=0, t=10, b=0),
            height=350,
            xaxis_title=None,
            yaxis_title="PnL ($)"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No closed trades yet.")

# 4. Trade Lists
st.markdown("---")
tab1, tab2 = st.tabs(["🟢 Active Positions", "📚 Trade History"])

with tab1:
    if active_trades:
        # Custom Card View for Active Trades
        for symbol, t in active_trades.items():
            with st.container():
                # Card Styling
                # We don't have real-time PnL here without query, use simplistic view or fetch
                pnl_color = "green"
                # Note: Real-time PnL requires fetching current price.
                # Use Entry for now.

                c_1, c_2, c_3, c_4 = st.columns(4)
                c_1.markdown(f"**{symbol}**")
                c_2.text(f"Side: {t['side']}")
                c_3.text(f"Entry: ${t['entry']:.4f}")
                c_4.text(f"Amount: {t['amount']:.4f}")
                st.markdown("---")
    else:
        st.info("No active positions.")

with tab2:
    if closed_trades:
        df_hist = pd.DataFrame(closed_trades)
        # Format columns
        df_hist = df_hist[['symbol', 'side', 'entry',
                           'pnl', 'exit_reason', 'closed_at']]
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.text("No history available.")

# Auto Refresh
time.sleep(30)  # Slower refresh to save resources
st.rerun()
