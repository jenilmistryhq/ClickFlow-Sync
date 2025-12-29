# ClickFlow-Sync 🚀
ClickFlow-Sync is an idempotent Python library that bridges external data sources (scanners, logs, pipelines) with ClickUp and Slack. It ensures tasks are never duplicated and allows team members to claim tickets directly from Slack.

## 🛠 Step 1: Installation
From PyPI (Recommended)
```
pip install clickflow-sync
```
From Source (Development)
```
git clone https://github.com/jenilmistryhq/ClickFlow-Sync.git
cd ClickFlow-Sync
pip install -r requirements.txt
```


## ⚙️ Step 2: Configuration
ClickFlow-Sync looks for environment variables to authenticate. Create a `.env` file in your project root:
```
# ClickUp Configuration
CLICKUP_API_KEY=pk_your_personal_api_key_here
CLICKUP_TEAM_ID=1234567
CLICKUP_LIST_ID=901234567890

# Slack Configuration (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T0000/B0000/XXXX
SLACK_BOT_TOKEN=xoxb-your-bot-token-here


# Default Assignment (Optional)
DEFAULT_ASSIGNEE_EMAIL=your_email@usedforclickup.com
```

## 🚀 Step 3: Usage in Your Project
Once installed, you can import ClickFlow-Sync into any script.
1. Pushing a Task to ClickUp & Slack
```
from clickflow_sync import ClickFlowEngine, ClickUpTask, SlackPlugin

# Initialize
engine = ClickFlowEngine()
slack = SlackPlugin()

# Define the task
task = ClickUpTask(
    internal_id="SEC-101", # Unique ID prevents duplicates
    title="Critical Vulnerability Found",
    description="Found SQLi on /api/login",
    priority=1,
    tags=["security", "automated"]
)

# Sync: Creates task in ClickUp and sends Slack message with "Claim" button
engine.upsert_task(task, callback=slack.send_notification)
```

## 🤖 Step 4: Setting up the "Claim Task" Bot
To make the Claim Task button work, you must run a small listener script (the Interaction Bot).
1. Create `app.py`. Copy this sample code into a file named `app.py`. This script listens for Slack button clicks.
```
import os
import json
import requests
import threading
import time
from datetime import datetime
from flask import Flask, request, make_response
from src.engine import ClickFlowEngine
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
engine = ClickFlowEngine()

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")

def background_worker(payload, slack_user_id, clickup_task_id, response_url):
    try:
        # 1. Fetch User Data
        user_info = requests.get(
            f"https://slack.com/api/users.info?user={slack_user_id}",
            headers={"Authorization": f"Bearer {SLACK_TOKEN}"}
        ).json()
        
        user_profile = user_info.get("user", {})
        slack_email = user_profile.get("profile", {}).get("email", "").lower()
        slack_display_name = user_profile.get("real_name") or user_profile.get("name") or "Team Member"

        if not engine.members:
            engine.members = engine._fetch_members()
        
        target_member_id = engine.members.get(slack_email, {}).get('id')
        if not target_member_id:
             # Fallback name search
             for email, info in engine.members.items():
                if slack_display_name.lower() in info.get('username', '').lower():
                    target_member_id = info['id']
                    break

        assignment_successful = False
        if target_member_id:
            clean_task_id = str(clickup_task_id).strip()
            assign_url = f"https://api.clickup.com/api/v2/task/{clean_task_id}/assignee/{target_member_id}"
            
            # STEP 1: Perform the assignment
            res = requests.post(assign_url, headers=engine.headers)
            
            if res.status_code in [200, 201]:
                time.sleep(1.5)
                check_res = requests.get(f"https://api.clickup.com/api/v2/task/{clean_task_id}", headers=engine.headers).json()
                assignees = [str(a['id']) for a in check_res.get('assignees', [])]
                
                if str(target_member_id) in assignees:
                    print(f"✅ VERIFIED: {slack_display_name} is in ClickUp.")
                    assignment_successful = True
            else:
                print(f"❌ ClickUp Rejected: {res.text}")
        
        updated_blocks = payload.get("message", {}).get("blocks", [])
        current_time = datetime.now().strftime("%I:%M %p")
        
        # Only show the Green Check if we VERIFIED the assignment
        status_text = f"✅ {slack_display_name}" if assignment_successful else f"⚠️ Syncing... (Click again in 2s)"

        for block in updated_blocks:
            if block.get("type") == "section" and "fields" in block:
                for field in block["fields"]:
                    if "*Assignees:*" in field.get("text", ""):
                        field["text"] = f"*Assignees:*\n{status_text}"
            
            if block.get("type") == "actions":
                # Only hide button if verified
                if assignment_successful:
                    block["elements"] = [btn for btn in block["elements"] if "url" in btn]

        updated_blocks = [b for b in updated_blocks if b.get("type") != "context"]
        updated_blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f":stopwatch: *Claimed at:* {current_time}  |  :user: *By:* {slack_display_name}"
            }]
        })

        requests.post(response_url, json={"replace_original": "true", "blocks": updated_blocks})

    except Exception as e:
        print(f"🔥 Worker Error: {e}")

@app.route("/slack/interactive", methods=["POST"])
def handle_interaction():
    payload = json.loads(request.form.get("payload"))
    try:
        action = payload["actions"][0]
        # Using .get to prevent the KeyError you saw in the logs
        task_id = action.get("value") or action.get("action_id")
        
        thread = threading.Thread(
            target=background_worker, 
            args=(payload, payload["user"]["id"], task_id, payload.get("response_url"))
        )
        thread.start()
    except Exception as e:
        print(f"🔥 Payload Error: {e}")
        
    return make_response("", 200)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
```

2. Connect Slack to your Computer (Local Testing)
Since Slack cannot "see" your laptop, use a tunnel:
* **Run your app:** `python app.py`
* **Open a tunnel:** `ssh -R 80:localhost:8000 nokey@localhost.run`
* **Update Slack:** Copy the `.lhr.life` URL provided and paste it into your Slack App Settings > Interactivity > Request URL, adding `/slack/interactive` at the end.

## 📝 Data Model (`ClickUpTask`)
```
 Field        | Type | Required | Description                                        
--------------|------|----------|----------------------------------------------------
 internal_id  | str  | Yes      | Unique reference (e.g., Jira ID, CVE ID).          
 title        | str  | Yes      | The name of the task in ClickUp.                   
 description  | str  | No       | Detailed content (supports Markdown).              
 priority     | int  | No       | 1 (Urgent), 2 (High), 3 (Normal), 4 (Low).         
 tags         | list | No       | List of strings (e.g., ["bug", "api"]).            
```


## 🏗 Key Features for Developers
1. **Idempotency:** The library tracks internal_id in sync_state.json. Running the same script twice will update the existing task instead of creating a new one.
2. **Thread Safety:** The Slack interaction handler uses background threading to ensure the Slack UI never times out (503 error).
3. **Verification:** Before showing a "Success" checkmark in Slack, the library re-queries the ClickUp API to verify the assignee was saved.

## 🤝 Contributing
1. Fork the repo
2. Create your feature branch `git checkout -b AmazingFeature`
3. Commit your changes `git commit -m 'Add AmazingFeature'`
4. Push to the branch `git push origin AmazingFeature`
5. Open a Pull Request