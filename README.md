# **ClickFlow-Sync 🚀**
ClickFlow-Sync is a professional, idempotent Python engine designed to bridge external
data sources (Vulnerability Scanners, Monitoring Tools, or CI/CD pipelines) with ClickUp.
Unlike a simple API wrapper, ClickFlow-Sync manages state. It ensures that if a scanner
finds the same issue twice, it updates the existing ClickUp task instead of creating
annoying duplicates.

---
### **📦 Installation**

#### **1. Clone the repository:**

```
git clone https://github.com/jenilmistryhq/ClickFlow-Sync.git
cd clickflow-sync
```
#### **2. Install Dependencies:**

```
pip install -r requirements.txt
```
---
### **⚙ Configuration (.env)**

The engine automatically looks for a `.env` file in your root directory. Create one with the
following variables:

```
# ClickUp Personal API Token (Settings > Apps)
CLICKUP_API_KEY=pk_your_api_key_here

# The Default List where tasks will be created
CLICKUP_LIST_ID=9012000000

# Default Assignee IDs (Comma-separated for multiple people)
CLICKUP_DEFAULT_ASSIGNEE=1234567,8901234
```

---
### **🛠 Usage Patterns**

ClickFlow-Sync is designed to be imported into your existing projects. You do not need to
modify the core library.

#### **1. Simple Integration (Zero Config)**
Uses the default settings and logging provided in your `.env`.

```
from src.engine import ClickFlowEngine
from src.models import ClickUpTask

# Initialize with .env defaults
engine = ClickFlowEngine()

# Define the task
# internal_id is the unique key from your scanner/source
task = ClickUpTask(
    internal_id="CVE-2024-001", 
    title="Critical Vulnerability Found",
    description="Found on Production Server-01",
    priority=1
)

# Run Sync
engine.upsert_task(task)
```

#### **2. Advanced Routing & Team Mapping**
You can inject custom logic to route tasks to different teams (Security vs. DevOps) or
different Folders/Lists.

```
from src.engine import ClickFlowEngine
from src.models import ClickUpTask

# 1. Map your own categories to ClickUp User IDs
MY_TEAM_MAP = {
    "security": [111222, 333444],
    "devops": [555666],
    "general": [777888]
}

# 2. Initialize engine with your custom map and a default list
engine = ClickFlowEngine(
    team_map=MY_TEAM_MAP, 
    default_list_id="9015000000"
)

# 3. Create a task for a specific team
# This will automatically assign the IDs in the 'security' map
new_task = ClickUpTask(
    internal_id="SCAN-99",
    category="security", 
    title="Unauthorized API Access",
    target_list_id="9016000000" # Optional: Override destination list
)

engine.upsert_task(new_task)
```
---

### **🏗 Architecture & State**

ClickFlow-Sync creates a `sync_state.json` file upon the first run.
* **Creation:** If `internal_id` is not found in `sync_state.json`, a new task is created and the ID is mapped.
* **Update:** If `internal_id` exists, the engine performs a `PUT` request to update the
existing task details.

---

### **📝 Data Model (ClickUpTask)**

```

| Field           | Type | Default      | Description                                                     |
|-----------------|------|--------------|-----------------------------------------------------------------|
| internal_id     | str  | Required     | The unique ID from your source system.                          |
| title           | str  | Required     | The ClickUp task name.                                          |
| description     | str  | ""           | The task body / content.                                       |
| category        | str  | "general"    | Used for looking up assignees in the Team Map.                  |
| priority        | int  | None         | 1 (Urgent), 2 (High), 3 (Normal), 4 (Low).                      |
| tags            | list | []           | List of strings to apply as ClickUp tags.                       |
| target_list_id  | str  | None         | Send the task to a specific ClickUp list.                       |

```

### **🤝 Contributing**
Contributions are welcome! Please open an issue or submit a pull request.