import os
import requests
import json
from datetime import datetime

class SlackPlugin:
    def __init__(self, webhook_url: str = None, member_info: dict = None):
        """
        member_info: Optional dict mapping ID to {'name': '...', 'dept': '...'}
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.member_info = member_info or {}

    def _get_member_string(self, assignee_ids):
        """Converts IDs to 'Name (Department)' strings."""
        if not assignee_ids:
            return None
        
        results = []
        for aid in assignee_ids:
            info = self.member_info.get(aid)
            if info:
                results.append(f"{info.get('name')} [{info.get('dept')}]")
            else:
                results.append(f"User ID: {aid}")
        return ", ".join(results)

    def default_formatter(self, task, clickup_id, action):
        """The default message logic with 'Empty Field Skipping'."""
        icon = "🆕" if action == "CREATED" else "🔄"
        prio_map = {1: "🔴 Urgent", 2: "🟠 High", 3: "🔵 Normal", 4: "⚪ Low"}
        
        # Gather data and filter out None/Empty values
        fields_data = {
            "Priority": prio_map.get(task.priority) if task.priority else None,
            "Category": task.category if task.category != "general" else None,
            "Tags": ", ".join(task.tags) if task.tags else None,
            "Assignees": self._get_member_string(task.assignees),
            "Internal ID": f"`{task.internal_id}`"
        }

        # Build Slack Blocks dynamically (Only adding non-empty fields)
        slack_fields = []
        for label, val in fields_data.items():
            if val: # Skip if empty or None
                slack_fields.append({"type": "mrkdwn", "text": f"*{label}:*\n{val}"})

        return {
            "text": f"ClickUp {action}: {task.title}",
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": f"{icon} Task {action}"}},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Title:* {task.title}"}},
                {"type": "section", "fields": slack_fields},
                {"type": "actions", "elements": [{
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Task ↗️"},
                    "url": f"https://app.clickup.com/t/{clickup_id}",
                    "style": "primary"
                }]}
            ]
        }

    def send_notification(self, task, clickup_id, action, custom_formatter=None):
        """
        The main callback. 
        custom_formatter: A function that takes (task, clickup_id, action) and returns a dict.
        """
        formatter = custom_formatter or self.default_formatter
        payload = formatter(task, clickup_id, action)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # --- ENHANCED LOCAL PREVIEW (Dynamic Filter) ---
        print("\n" + "═"*60)
        print(f"🖥️  LOCAL NOTIFICATION PREVIEW | {current_time}")
        print("═"*60)
        print(f"EVENT:      [{action}]")
        print(f"TITLE:      {task.title}")
        
        # Only print fields that exist
        assignee_str = self._get_member_string(task.assignees)
        if assignee_str: print(f"ASSIGNEES:  {assignee_str}")
        if task.priority: print(f"PRIORITY:   {task.priority}")
        if task.tags:     print(f"TAGS:       {task.tags}")
        
        print(f"URL:        https://app.clickup.com/t/{clickup_id}")
        
        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json=payload)
                print("🚀 Sent successfully to Slack!")
            except Exception as e:
                print(f"❌ Slack Error: {e}")
        else:
            print("-"*60)
            print("ℹ️  Webhook URL missing. Outputting local preview only.")
        print("═"*60 + "\n")