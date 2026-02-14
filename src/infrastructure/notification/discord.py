import requests
from datetime import datetime
from src.config.settings import DISCORD_WEBHOOK_URL


def log_to_discord(message, level="info"):
    if not DISCORD_WEBHOOK_URL:
        return
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = 3447003 if level == "info" else 15158332
    try:
        requests.post(
            DISCORD_WEBHOOK_URL,
            json={
                "embeds": [
                    {"description": f"**[{timestamp}]** {message}",
                        "color": color}
                ]
            },
        )
    except:
        pass
