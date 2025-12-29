import os
import requests
import datetime
import json
from .state_provider import JSONStateProvider

class ClickFlowEngine:
    def __init__(self, state_provider=None):
        self.api_key = os.getenv("CLICKUP_API_KEY")
        self.team_id = os.getenv("CLICKUP_TEAM_ID")
        self.list_id = os.getenv("CLICKUP_LIST_ID")
        
        # Defensive check for API Key
        if not self.api_key:
            raise ValueError("CLICKUP_API_KEY not found in environment variables")
            
        self.headers = {
            "Authorization": self.api_key, 
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.clickup.com/api/v2"
        self.state = state_provider or JSONStateProvider()
        self.members = self._fetch_members()

    def _fetch_members(self):
        try:
            res = requests.get(f"{self.base_url}/team/{self.team_id}", headers=self.headers)
            if res.status_code == 200:
                return {m['user']['email'].lower().strip(): m['user'] for m in res.json()['team']['members']}
        except Exception as e:
            print(f"⚠️ Member fetch failed: {e}")
        return {}

    def upsert_task(self, task, callback=None):
        clickup_id = self.state.get(task.internal_id)
        
        # Get assignee IDs
        assignee_ids = []
        for email in task.assignee_emails:
            member = self.members.get(email.lower().strip())
            if member:
                assignee_ids.append(int(member['id']))

        payload = {
            "name": task.title,
            "description": task.description,
            "status": task.status.lower(),
            "priority": task.priority,
            "assignees": assignee_ids,
            "tags": task.tags
        }

        if clickup_id:
            url = f"{self.base_url}/task/{clickup_id}"
            res = requests.put(url, headers=self.headers, json=payload)
            if res.status_code == 404:
                print("⚠️ Ghost task found. Re-creating...")
                self.state.set(task.internal_id, None)
                return self.upsert_task(task, callback)
        else:
            url = f"{self.base_url}/list/{self.list_id}/task"
            res = requests.post(url, headers=self.headers, json=payload)

        # Handle Status Errors
        if res.status_code == 400 and "Status not found" in res.text:
            payload.pop("status")
            res = requests.post(url, headers=self.headers, json=payload)

        if res.status_code in [200, 201]:
            data = res.json()
            new_id = data['id']
            self.state.set(task.internal_id, new_id) # This creates the JSON file
            
            if task.attachment_paths:
                self._upload_files(new_id, task.attachment_paths)
            if callback:
                callback(task, new_id, "SYNCED", self.members, assignee_ids)
            return new_id
        
        print(f"❌ ClickUp Error: {res.text}")
        return None

    def _upload_files(self, clickup_id, paths):
        url = f"{self.base_url}/task/{clickup_id}/attachment"
        # No Content-Type for file uploads
        headers = {"Authorization": self.api_key}
        for path in paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    files = {'attachment': (os.path.basename(path), f)}
                    requests.post(url, headers=headers, files=files)