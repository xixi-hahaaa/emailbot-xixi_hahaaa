"""
    Discord Webhook - IGNORE
"""

import requests
import json

from query import load_query

class DiscordNotifier:
    def __init__(self):
        json_file = "json/discord.json"
        queries = load_query(json_file)
        webhook = queries.get("channel_url")
        self.webhook_url = webhook

    def send_notification(self, message):
        """Send a message to Discord using the webhook URL."""
        payload = {
            "content": message
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(
            self.webhook_url,
            data=json.dumps(payload),
            headers=headers
        )

        if response.status_code == 204:
            print("Notification sent successfully.")
        else:
            print(f"Failed to send notification. Status code: {response.status_code}, Response: {response.text}")