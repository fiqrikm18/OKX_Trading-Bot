import streamlit as st
import pandas as pd
import plotly.express as px
import time
from src.infrastructure.persistence.postgres_repo import PostgresRepository
from src.config.settings import INITIAL_PAPER_BALANCE

# Page Config
st.set_page_config(page_title="OKX AI Bot Dashboard",
                   layout="wide", page_icon="🤖")


@st.cache_resource
def get_repo(v=1):
    return PostgresRepository()


repo = get_repo(v=2)

# Session State for Auth
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False


def login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if repo.verify_user(username, password):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid username or password")


def logout():
    st.session_state["authenticated"] = False
    st.rerun()


# Default to Login if not authenticated
if not st.session_state["authenticated"]:
    login()
    st.stop()

# Sidebar
st.sidebar.title("🤖 Bot Controls")
if st.sidebar.button("Refresh Data"):
    st.rerun()

if st.sidebar.button("Logout"):
    logout()

# Fetch Data
state_bal = repo.load_state_value("paper_balance", INITIAL_PAPER_BALANCE)
total_pnl = repo.load_state_value("total_pnl", 0.0)
trades = repo.load_trades()

# Top Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Paper Balance", f"${state_bal:.2f}")
col2.metric("Total PnL", f"${total_pnl:.2f}",
            delta_color="normal" if total_pnl >= 0 else "inverse")
col3.metric("Active Positions", len(trades))

# Active Trades
st.subheader("📊 Active Trades")
if trades:
    df_trades = pd.DataFrame(trades.values())
    st.dataframe(df_trades)
else:
    st.info("No active trades.")

# Equity Curve
st.subheader("📈 Equity Curve")
try:
    history = repo.load_equity_history()

    if history:
        df_history = pd.DataFrame(history)
        fig = px.line(df_history, x="timestamp",
                      y="equity", title="Equity Over Time")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No equity history yet.")
except Exception as e:
    st.error(f"Error fetching history: {e}")

# Auto Refresh
time.sleep(10)
st.rerun()
