import os
import requests

class SlackPlugin:
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    def send_notification(self, task, clickup_id, action, member_map, resolved_ids):
        # We use a specific structure so we can target fields for updates later
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🛡️ Vulnerability {action}"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn", 
                    "text": f"*Title:* <https://app.clickup.com/t/{clickup_id}|{task.title}>\n*Status:* `{task.status.upper()}`"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Assignees:*\nUnassigned"},
                    {"type": "mrkdwn", "text": f"*Internal ID:*\n`{task.internal_id}`"}
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Ticket ↗️"},
                        "url": f"https://app.clickup.com/t/{clickup_id}"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🙋 Claim Task"},
                        "style": "primary",
                        "value": clickup_id,
                        "action_id": "claim_task"
                    }
                ]
            }
        ]
        
        if self.webhook_url:
            requests.post(self.webhook_url, json={"blocks": blocks})