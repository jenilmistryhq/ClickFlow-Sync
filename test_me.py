from src.engine import ClickSyncEngine
from src.models import ClickUpTask

def run():
    engine = ClickSyncEngine()

    # Minimal task data
    task_data = ClickUpTask(
        internal_id="simple_test_001",
        title="Testing Simple Task",
        description="No assignment, just checking connection."
    )

    print("--- Starting Sync ---")
    engine.upsert_task(task_data)

if __name__ == "__main__":
    run()