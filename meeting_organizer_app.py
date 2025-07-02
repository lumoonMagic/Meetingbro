# meeting_organizer_app.py

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import uuid
import requests
import base64
from apscheduler.schedulers.background import BackgroundScheduler

# ------------------------ CONFIG ------------------------ #
st.set_page_config(page_title="Meeting Organizer", layout="wide")

# Store your Teams webhook here or via Streamlit secrets
if "webhook_url" not in st.session_state:
    st.session_state["webhook_url"] = ""

# ------------------------ DATA STRUCTURES ------------------------ #
if "meetings" not in st.session_state:
    st.session_state["meetings"] = []

if "action_items" not in st.session_state:
    st.session_state["action_items"] = []

if "summary_chunks" not in st.session_state:
    st.session_state["summary_chunks"] = []

# ------------------------ HELPERS ------------------------ #
def generate_meeting_html(meeting, summary_chunks, action_items):
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            h1 {{ color: #444; }}
            .summary {{ margin-bottom: 30px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            th {{ background-color: #f4f4f4; }}
        </style>
    </head>
    <body>
        <h1>Meeting Summary: {meeting['title']}</h1>
        <p><strong>Date:</strong> {meeting['date']}</p>
        <p><strong>Participants:</strong> {', '.join(meeting['participants'])}</p>
        <div class="summary">
            <h2>Summary</h2>
            <ul>
                {''.join([f'<li>{point}</li>' for point in summary_chunks])}
            </ul>
        </div>
        <div class="actions">
            <h2>Action Items</h2>
            <table>
                <tr><th>Task</th><th>Assignee</th><th>Due Date</th><th>Status</th></tr>
                {''.join([f"<tr><td>{item['task']}</td><td>{item['assignee']}</td><td>{item['due_date']}</td><td>{item['status']}</td></tr>" for item in action_items])}
            </table>
        </div>
    </body>
    </html>
    """
    return html

def get_download_link(html, filename="meeting.html"):
    b64 = base64.b64encode(html.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}" target="_blank">📄 Download MoM as HTML</a>'

def send_to_teams(meeting, summary_url, webhook_url):
    message = {
        "text": f"*Meeting Summary:* {meeting['title']}\n\nDate: {meeting['date']}\nParticipants: {', '.join(meeting['participants'])}\n\n👉 [View MoM]({summary_url})"
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, json=message, headers=headers)
    return response.status_code

# ------------------------ MAIN UI ------------------------ #
st.title("📅 Meeting Organizer with MoM Generator")

st.sidebar.header("🔧 Configuration")
st.session_state["webhook_url"] = st.sidebar.text_input("Teams Webhook URL", st.session_state["webhook_url"])

# Meeting form
with st.form("meeting_form"):
    st.subheader("📝 Start New Meeting")
    title = st.text_input("Meeting Title")
    date = st.date_input("Meeting Date", value=datetime.today())
    participants = st.text_input("Participants (comma-separated)")
    notes = st.text_area("Meeting Notes")
    submitted = st.form_submit_button("Start Meeting")

    if submitted:
        meeting = {
            "id": str(uuid.uuid4()),
            "title": title,
            "date": str(date),
            "participants": [p.strip() for p in participants.split(",")],
            "notes": notes
        }
        st.session_state.meetings.append(meeting)
        st.success("Meeting started and saved.")

# Action items
st.subheader("📌 Action Items")
with st.form("action_form"):
    task = st.text_input("Task")
    assignee = st.text_input("Assign To")
    due_date = st.date_input("Due Date", value=datetime.today() + timedelta(days=3))
    status = st.selectbox("Status", ["Pending", "In Progress", "Done"])
    add_task = st.form_submit_button("Add Action Item")

    if add_task:
        st.session_state.action_items.append({
            "task": task,
            "assignee": assignee,
            "due_date": str(due_date),
            "status": status
        })
        st.success("Action item added.")

# Summarization (mocked here for simplicity)
st.subheader("🧠 Meeting Summary")
if st.button("🔄 Generate Final Summary"):
    # Mocked summary (replace with LLM call in real usage)
    st.session_state.summary_chunks = [
        "Discussed project timelines.",
        "Assigned new tasks to the frontend team.",
        "Budget review pending for Q3."
    ]
    st.success("Summary generated.")

if st.session_state.summary_chunks:
    st.markdown("### 🔍 Current Summary")
    for point in st.session_state.summary_chunks:
        st.markdown(f"- {point}")

# HTML output
st.subheader("📤 Export & Share")
if st.button("📄 Generate MoM HTML"):
    if not st.session_state.meetings:
        st.warning("No meeting found.")
    else:
        meeting = st.session_state.meetings[-1]
        html = generate_meeting_html(meeting, st.session_state.summary_chunks, st.session_state.action_items)
        components.html(html, height=600, scrolling=True)
        st.markdown(get_download_link(html), unsafe_allow_html=True)

        if st.session_state.webhook_url:
            st.info("Sending to Teams...")
            # For simplicity, we assume local app, so we can't give a live URL
            response = send_to_teams(meeting, "(MoM attached via Streamlit)", st.session_state.webhook_url)
            if response == 200:
                st.success("✅ Sent to Microsoft Teams.")
            else:
                st.error(f"❌ Failed to send to Teams. Status: {response}")
