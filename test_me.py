from src.engine import ClickFlowEngine
from src.models import ClickUpTask
from src.slack_plugin import SlackPlugin

def run_test():
    # 1. Setup
    engine = ClickFlowEngine()
    slack = SlackPlugin() # Automatically reads .env

    # 2. Define a detailed task
    test_task = ClickUpTask(
        internal_id="SCAN-2025-X",
        title="[CRITICAL] SQL Injection - Login Page",
        description="Vulnerability found in /api/auth/login endpoint. Immediate patch required.",
        priority=1,
        category="security"
    )

    # 3. Sync with Slack Callback
    print("--- Starting ClickFlow Sync ---")
    engine.upsert_task(test_task, callback=slack.send_notification)

if __name__ == "__main__":
    run_test()