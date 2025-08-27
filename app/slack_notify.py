import os
import requests


def send_slack_alert(message: str):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False
    payload = {"text": message}
    resp = requests.post(webhook_url, json=payload)
    return resp.status_code == 200
