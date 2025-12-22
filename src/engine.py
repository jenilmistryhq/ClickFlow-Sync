import os
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from .models import ClickUpTask

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("ClickFlow")

class ClickFlowEngine:
    def __init__(self, team_map: dict = None, default_list_id: str = None):
        load_dotenv()
        self.api_key = str(os.getenv("CLICKUP_API_KEY")).strip()
        self.state_file = "sync_state.json"
        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {"Authorization": self.api_key, "Content-Type": "application/json"}
        
        self.default_list_id = default_list_id or os.getenv("CLICKUP_LIST_ID")
        
        raw_ids = os.getenv("CLICKUP_DEFAULT_ASSIGNEE", "")
        env_assignees = [int(i.strip()) for i in raw_ids.split(",") if i.strip()]
        self.team_map = team_map or {"general": env_assignees}
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f: return json.load(f)
        return {}

    def _save_state(self):
        with open(self.state_file, "w") as f: json.dump(self.state, f, indent=4)

    def upsert_task(self, task: ClickUpTask, callback=None):
        internal_key = str(task.internal_id)
        clickup_id = self.state.get(internal_key)
        dest_list = task.target_list_id or self.default_list_id
        assignees = task.assignees or self.team_map.get(task.category, self.team_map.get("general", []))

        payload = {
            "name": task.title,
            "description": task.description,
            "assignees": assignees,
            "priority": task.priority,
            "tags": task.tags
        }

        try:
            # 1. ATTEMPT UPDATE IF ID EXISTS
            if clickup_id:
                url = f"{self.base_url}/task/{clickup_id}"
                response = requests.put(url, headers=self.headers, json=payload)
                
                # FIX: If ClickUp says Task is deleted (ITEM_013), clear state and go to CREATE
                if response.status_code == 404:
                    logger.warning(f"⚠️ Task {clickup_id} was deleted in ClickUp. Re-creating...")
                    del self.state[internal_key]
                    clickup_id = None 
                else:
                    action = "UPDATED"

            # 2. ATTEMPT CREATE IF NO ID (OR IF PREVIOUS UPDATE FAILED)
            if not clickup_id:
                url = f"{self.base_url}/list/{dest_list}/task"
                response = requests.post(url, headers=self.headers, json=payload)
                action = "CREATED"
            
            if response.status_code == 200:
                data = response.json()
                res_id = data.get('id', clickup_id)
                self.state[internal_key] = res_id
                self._save_state()

                if callback:
                    callback(task, res_id, action)
                return res_id
            
            logger.error(f"❌ API Error: {response.text}")
        except Exception as e:
            logger.error(f"❌ System Error: {str(e)}")
        return None