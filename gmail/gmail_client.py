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
