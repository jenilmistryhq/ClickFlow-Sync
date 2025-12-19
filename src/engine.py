import os
import json
import logging
import requests
from dotenv import load_dotenv
from .models import ClickUpTask

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ClickSync")

class ClickSyncEngine:
    def __init__(self):
        load_dotenv()
        # Use .strip() to ensure no hidden spaces/newlines from the .env file
        self.api_key = str(os.getenv("CLICKUP_API_KEY")).strip()
        self.list_id = str(os.getenv("CLICKUP_LIST_ID")).strip()
        self.state_file = "sync_state.json"
        self.base_url = "https://api.clickup.com/api/v2"

        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {}

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=4)

    def upsert_task(self, task: ClickUpTask):
        clickup_id = self.state.get(str(task.internal_id))
        
        # Minimalist payload: No assignees, no priority
        payload = {
            "name": task.title,
            "description": task.description,
            "status": task.status
        }

        # ONLY add status if it's not None
        if task.status:
            payload["status"] = task.status

        try:
            if clickup_id:
                url = f"{self.base_url}/task/{clickup_id}"
                response = requests.put(url, headers=self.headers, json=payload)
                if response.status_code == 200:
                    logger.info(f"✅ UPDATED: {task.internal_id}")
                    return clickup_id
            else:
                url = f"{self.base_url}/list/{self.list_id}/task"
                response = requests.post(url, headers=self.headers, json=payload)
                
                if response.status_code == 200:
                    new_id = response.json()["id"]
                    self.state[str(task.internal_id)] = new_id
                    self._save_state()
                    logger.info(f"🚀 CREATED: {new_id}")
                    return new_id
            
            # If we didn't get a 200, log the exact reason
            logger.error(f"❌ API REJECTED ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"❌ CONNECTION ERROR: {str(e)}")
        
        return None