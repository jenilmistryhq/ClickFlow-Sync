from src.engine import ClickFlowEngine
from src.models import ClickUpTask

def run_test():
    engine = ClickFlowEngine()

    # This task will use the 'general' category, 
    # which we mapped to the multiple IDs in your .env
    test_task = ClickUpTask(
        internal_id="MULTI-ASSIGN-01",
        category="general", 
        title="Testing Multiple Assignees",
        description="This task should have two people assigned automatically.",
        priority=3
    )

    print("--- 🚀 Testing Multi-Assignee Logic ---")
    engine.upsert_task(test_task)

if __name__ == "__main__":
    run_test()