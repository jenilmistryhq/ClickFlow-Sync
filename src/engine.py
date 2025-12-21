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
        
        # Configurable Defaults
        self.default_list_id = default_list_id or os.getenv("CLICKUP_LIST_ID")
        
        # Fallback to .env for "general" team if no map is provided
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

    def _default_callback(self, task: ClickUpTask, clickup_id: str, action: str):
        """The default behavior if the user doesn't provide a custom one."""
        logger.info(f"✅ {action}: {task.title} (Internal: {task.internal_id}) -> ClickUp: {clickup_id}")

    def upsert_task(self, task: ClickUpTask, callback=None):
        """
        Creates or Updates a task. 
        callback: function(task, clickup_id, action) -> Optional custom action on success.
        """
        clickup_id = self.state.get(str(task.internal_id))
        
        # Routing Logic
        dest_list = task.target_list_id if task.target_list_id else self.default_list_id
        
        # Assignment Logic
        current_assignees = task.assignees
        if not current_assignees:
            current_assignees = self.team_map.get(task.category, self.team_map.get("general", []))

        payload = {
            "name": task.title,
            "description": task.description,
            "assignees": current_assignees,
            "priority": task.priority,
            "tags": task.tags,
            "due_date": task.due_date
        }

        try:
            if clickup_id:
                url = f"{self.base_url}/task/{clickup_id}"
                response = requests.put(url, headers=self.headers, json=payload)
                action = "UPDATED"
            else:
                url = f"{self.base_url}/list/{dest_list}/task"
                response = requests.post(url, headers=self.headers, json=payload)
                action = "CREATED"
            
            if response.status_code == 200:
                data = response.json()
                res_id = data.get('id', clickup_id)
                
                # Save state only on creation
                if not clickup_id:
                    self.state[str(task.internal_id)] = res_id
                    self._save_state()
                    
                # --- CALLBACK TRIGGER ---
                # Use the user's callback if provided, otherwise use default
                final_callback = callback if callback else self._default_callback
                final_callback(task, res_id, action)
                
                return res_id
            
            logger.error(f"❌ API Error: {response.text}")
        except Exception as e:
            logger.error(f"❌ System Error: {str(e)}")
        return None