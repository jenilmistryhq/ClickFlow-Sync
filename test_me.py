import os
import time
from dotenv import load_dotenv

# CRITICAL: Load the .env file before importing the engine
load_dotenv()

from src.engine import ClickFlowEngine
from src.models import ClickUpTask
from src.slack_plugin import SlackPlugin

def run_diagnostic():
    # 1. Clear old state to ensure a fresh test
    if os.path.exists("sync_state.json"):
        os.remove("sync_state.json")
        print("🧹 Cache cleared.")

    # 2. Check if API Key actually loaded
    api_key = os.getenv("CLICKUP_API_KEY")
    if not api_key:
        print("❌ ERROR: CLICKUP_API_KEY is empty! Check your .env file.")
        return
    else:
        print(f"🔑 API Key loaded: {api_key[:5]}***")

    engine = ClickFlowEngine()
    slack = SlackPlugin()
    
    unique_id = f"FINAL-TEST-{int(time.time())}"
    
    task = ClickUpTask(
        internal_id=unique_id,
        title=f"Authorization Fix Test ({unique_id})",
        description="Verifying OAUTH_017 fix and sync_state creation.",
        status="not started", 
        priority=1,
        assignee_emails=[os.getenv("DEFAULT_ASSIGNEE_EMAIL", "")]
    )

    print(f"🚀 Running Sync for {unique_id}...")
    task_id = engine.upsert_task(task, callback=slack.send_notification)

    if task_id:
        print(f"✅ Success! ClickUp ID: {task_id}")
        print(f"📂 sync_state.json should now exist in your folder.")
    else:
        print("❌ Sync Failed. Check the error message above.")

if __name__ == "__main__":
    run_diagnostic()