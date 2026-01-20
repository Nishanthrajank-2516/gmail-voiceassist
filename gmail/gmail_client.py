import os
import base64
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

TOKEN_PATH = "config/token.json"
CREDENTIALS_PATH = "config/credentials.json"


def authenticate_gmail():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH, SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def send_email(service, to_email, subject, body):
    message = MIMEText(body)
    message["to"] = to_email
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {"raw": raw}

    sent = (
        service.users()
        .messages()
        .send(userId="me", body=message_body)
        .execute()
    )

    return sent["id"]
def get_latest_email(service):
    results = (
        service.users()
        .messages()
        .list(userId="me", maxResults=1, labelIds=["INBOX"])
        .execute()
    )

    messages = results.get("messages", [])
    if not messages:
        return None

    msg_id = messages[0]["id"]

    message = (
        service.users()
        .messages()
        .get(userId="me", id=msg_id, format="metadata")
        .execute()
    )

    headers = message["payload"]["headers"]

    subject = ""
    sender = ""

    for h in headers:
        if h["name"] == "Subject":
            subject = h["value"]
        if h["name"] == "From":
            sender = h["value"]

    return {
        "id": msg_id,
        "subject": subject,
        "from": sender
    }


def delete_email(service, msg_id):
    service.users().messages().trash(
        userId="me",
        id=msg_id
    ).execute()
    return True


def get_emails_from_sender(service, sender_email, max_results=3):
    query = f"from:{sender_email}"

    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        full = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full"
        ).execute()

        headers = full["payload"].get("headers", [])
        subject = ""
        sender = ""

        for h in headers:
            if h["name"] == "Subject":
                subject = h["value"]
            elif h["name"] == "From":
                sender = h["value"]

        emails.append({
            "id": msg["id"],
            "subject": subject,
            "from": sender,
            "raw": full
        })

    return emails



import base64
from email.message import EmailMessage

def reply_to_email(service, original_email, reply_text):
    """
    Reply to an email safely, even if 'raw' is missing.
    """

    # 🔄 Ensure full message is available
    if "raw" not in original_email:
        msg = service.users().messages().get(
            userId="me",
            id=original_email["id"],
            format="full"
        ).execute()
    else:
        msg = original_email["raw"]

    headers = msg["payload"]["headers"]

    def get_header(name):
        for h in headers:
            if h["name"].lower() == name.lower():
                return h["value"]
        return ""

    to_email = get_header("From")
    subject = get_header("Subject")
    message_id = get_header("Message-ID")

    reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

    message = MIMEText(reply_text)
    message["To"] = to_email
    message["Subject"] = reply_subject
    message["In-Reply-To"] = message_id
    message["References"] = message_id

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": raw}
    ).execute()

def get_read_emails(service, max_results=20):
    results = service.users().messages().list(
        userId="me",
        q="-label:UNREAD",
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    return messages
