from flask import current_app as app
import requests

def send_discord_webhook(embeds):
    webhook_url = app.config.get("DISCORD_WEBHOOK_URL")
    if webhook_url is None:
        return

    requests.post(webhook_url, json={
        "embeds": embeds,
        "username": "CTFd",
        "avatar_url": app.config.get("DISCORD_AVATAR_URL")
    })
