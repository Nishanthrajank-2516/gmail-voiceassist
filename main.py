import threading
import webbrowser
from web.app import start_web
import shared_state

threading.Thread(target=start_web, daemon=True).start()

webbrowser.open("http://127.0.0.1:5000")

import os
import sys

def app_path(*paths):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *paths)

def ensure_audio_path(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

from audio.recorder import record_audio
from stt.whisper_engine import transcribe
from utils.contacts import resolve_contact
from gmail.gmail_client import get_unread_emails
from llm.intent_engine import extract_intent
from llm.intent_utils import normalize_intent

from gmail.gmail_client import (
    authenticate_gmail,
    send_email,
    get_latest_email,
    delete_email,
    get_emails_from_sender,
    reply_to_email,
)

from tts.speaker import speak
from utils.email_analyzer import analyze_email, html_to_text
import time


# 🔊 Wake words
WAKE_WORDS = ["zara", "sara","sarah", "sala"]

# 💤 Session exit (sleep)
EXIT_WORDS = ["cancel", "stop", "go to sleep", "sleep"]

# ❌ Hard exit (terminate program)
SHUTDOWN_WORDS = ["bye", "exit", "quit"]


def is_wake_word(text: str) -> bool:
    text = text.lower()
    return any(wake in text for wake in WAKE_WORDS)


def is_exit(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in EXIT_WORDS)


def is_shutdown(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in SHUTDOWN_WORDS)


def is_positive(text: str) -> bool:
    text = text.lower()
    return any(
        word in text
        for word in ["yes", "yeah", "sure", "ok", "okay", "read", "delete", "reply", "forward", "send"]
    )


import re

def pick_index(text: str) -> int | None:
    if not text:
        return None

    text = text.lower()

    # 🔹 Remove filler words & punctuation
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    word_map = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }

    # 1️⃣ DIGITS FIRST (highest priority)
    numbers = re.findall(r"\b\d+\b", text)
    if numbers:
        idx = int(numbers[0]) - 1
        return idx if idx >= 0 else None

    # 2️⃣ WORD NUMBERS
    for word, num in word_map.items():
        if re.search(rf"\b{word}\b", text):
            return num - 1

    return None



def ask_and_handle_reply(service, email_obj):
    shared_state.current_action = "replying"
    speak("Do you want to reply or forward this email?")
    shared_state.assistant_state = "speaking"
    path=app_path("audio","action_confirm.wav")
    ensure_audio_path(path)
    record_audio(path)
    action = transcribe(path).lower()

    # ✉️ REPLY
    if "reply" in action:
        speak("Please tell your reply. I am listening.")
        shared_state.assistant_state = "speaking"
        path = app_path("audio", "reply_body.wav")
        ensure_audio_path(path)

        # 🎙 listen for 10 seconds
        record_audio_seconds(path, 10)
        raw_reply = transcribe(path)

        # ✨ enhance (grammar + clarity ONLY)
        enhanced_reply = enhance_email_body(raw_reply)

        # 🔊 read back for confirmation
        speak("Here is your reply")
        speak(enhanced_reply)
        shared_state.assistant_state = "speaking"
        speak("Do you want me to send this reply?")
        path = app_path("audio", "reply_confirm.wav")
        ensure_audio_path(path)
        record_audio(path)
        confirm = transcribe(path)

        if not is_positive(confirm):
            speak("Reply cancelled")
            return

        reply_to_email(service, email_obj, enhanced_reply)
        speak("Reply sent successfully")

    # 📤 FORWARD
    elif "forward" in action:
        shared_state.current_action = "forwarding email"
        shared_state.assistant_state = "speaking"
        speak("Please say the name of the contact to forward to")
        path=app_path("audio","forward_to.wav")
        ensure_audio_path(path)
        record_audio(path)
        name = transcribe(path)

        to_email = resolve_contact(name)

        if not to_email:
            speak("I could not find that contact")
            return

        speak(f"Do you want me to forward this email to {name}?")
        path=app_path("audio","forward_confirm.wav")
        ensure_audio_path(path)
        record_audio(path)
        confirm = transcribe(path)

        if not is_positive(confirm):
            speak("Forward cancelled")
            return

        from gmail.gmail_client import forward_email
        forward_email(service, email_obj, to_email)
        speak("Email forwarded successfully")

from audio.recorder import record_audio_seconds
from llm.email_enhancer import enhance_email_body

def guided_send_email(service):
    shared_state.current_action = "sending email"
    # 1️⃣ Recipient
    shared_state.assistant_state = "speaking"
    speak("Whom should I send the email to?")
    path = app_path("audio", "send_to.wav")
    ensure_audio_path(path)
    record_audio(path)
    name = transcribe(path)

    to_email = resolve_contact(name)
    if not to_email:
        speak("I could not find that contact")
        return

    # 2️⃣ Subject
    speak("What is the subject?")
    path = app_path("audio", "send_subject.wav")
    ensure_audio_path(path)
    record_audio(path)
    subject = transcribe(path)

    # 3️⃣ Body (10 seconds)
    speak("Please tell the email body. I am listening.")

    path = app_path("audio", "send_body.wav")
    ensure_audio_path(path)
    record_audio_seconds(path, 10)
    raw_body = transcribe(path)

    # 4️⃣ Enhance body
    enhanced_body = enhance_email_body(raw_body)

    # 5️⃣ Read back
    speak(f"Sending email to {name}")
    speak(f"Subject: {subject}")
    speak("Here is the email content")
    speak(enhanced_body)

    # 6️⃣ Confirmation
    speak("Do you want me to send this email?")
    path = app_path("audio", "send_confirm.wav")
    ensure_audio_path(path)
    record_audio(path)
    confirm = transcribe(path)

    if not is_positive(confirm):
        speak("Email cancelled")
        return

    # 7️⃣ Send
    send_email(
        service,
        to_email=to_email,
        subject=subject,
        body=enhanced_body,
    )

    speak("Email sent successfully")


def handle_command(service) -> bool:
    intent = {"intent": None}

    path=app_path("audio","input.wav")  
    ensure_audio_path(path)
    record_audio(path)
    text = transcribe(path)

    print("You said:", text)

    # 🛑 Hard shutdown
    if is_shutdown(text):
        speak("Goodbye. Shutting down.")
        sys.exit(0)

    # 💤 Session exit
    if is_exit(text):
        speak("Okay. Going back to sleep.")
        return False

    intent_raw = extract_intent(text)
    intent = normalize_intent(intent_raw)

    print("Intent:", intent)
    shared_state.current_intent = intent["intent"]

    # 🔁 INTENT UPGRADES (NO FEATURE REMOVAL)
    if intent["intent"] == "READ_LATEST_EMAIL" and intent.get("to"):
        intent["intent"] = "READ_EMAIL_FROM_SENDER"

    if intent["intent"] == "DELETE_LATEST_EMAIL" and intent.get("to"):
        intent["intent"] = "DELETE_EMAIL_FROM_SENDER"

    # 📧 SEND EMAIL
    if intent["intent"] == "SEND_EMAIL":
        guided_send_email(service)


    # 📖 READ LATEST EMAIL
    elif intent["intent"] == "READ_LATEST_EMAIL":
        shared_state.current_action = "reading email"
        email = get_latest_email(service)
        if not email:
            speak("Your inbox is empty")
            return True

        speak(f"Email from {email['from']}")
        speak(f"Subject {email['subject']}")

        analysis = analyze_email(email)

        if analysis["has_html"]:
            speak("This email contains formatted HTML content")
        if analysis["has_images"]:
            speak("This email contains images")
        if analysis["attachments"]:
            speak(f"This email has {len(analysis['attachments'])} attachments")

        speak("Do you want me to read the email body?")
        path=app_path("audio","confirm.wav")
        ensure_audio_path(path)
        record_audio(path)
        reply = transcribe(path)

        if is_positive(reply):
            if email.get("body"):
                speak(email["body"])
            elif email.get("html"):
                speak("Reading extracted text from HTML email")
                speak(html_to_text(email["html"]))
            else:
                speak("This email does not contain readable text")

            ask_and_handle_reply(service, email)

    # 📥 LIST & READ UNREAD EMAILS
    elif intent["intent"] == "READ_UNREAD_EMAILS":
        shared_state.current_action = "reading email"
        emails = get_unread_emails(service, max_results=10)

        if not emails:
            speak("You have no unread emails")
            return True

        speak(f"here are the last {len(emails)} unread emails")

        for i, mail in enumerate(emails, start=1):
            speak(f"Email {i} from {mail['from']} with subject {mail['subject']}")

        speak("Which email should I read? Say a number between one and ten.")
        path=app_path("audio","choice.wav")
        ensure_audio_path(path)
        record_audio(path)
        choice_text = transcribe(path)

        idx = pick_index(choice_text)
        if idx is None or idx >= len(emails):
            speak("Invalid choice")
            return True

        selected = emails[idx]

        speak(f"Reading email from {selected['from']}")
        speak(f"Subject {selected['subject']}")

        snippet = selected["raw"].get("snippet")
        if snippet:
            speak(snippet)

        # Ask for reply
        ask_and_handle_reply(service, selected)

        # Ask for delete
        speak("Do you want to move this email to trash?")
        path=app_path("audio","confirm.wav")
        ensure_audio_path(path)
        record_audio(path)
        confirm = transcribe(path)

        if is_positive(confirm):
            delete_email(service, selected["id"])
            speak("Email moved to trash")

    # 📬 READ EMAILS FROM SENDER
    elif intent["intent"] == "READ_EMAIL_FROM_SENDER":
        shared_state.current_action = "reading email"
        sender_name = intent.get("to")
        sender_email = resolve_contact(sender_name) or sender_name

        emails = get_emails_from_sender(service, sender_email)

        if not emails:
            speak(f"No recent emails from {sender_name}")
            return True

        speak(f"Here are the last {len(emails)} emails from {sender_name}")

        for i, mail in enumerate(emails, start=1):
            speak(f"Email {i}: {mail['subject']}")

        speak("Which email should I read? Say one, two, or three.")
        path=app_path("audio","choice.wav")
        ensure_audio_path(path)
        record_audio(path)
        choice_text = transcribe(path)

        idx = pick_index(choice_text)
        if idx is None or idx >= len(emails):
            speak("Invalid choice")
            return True

        selected = emails[idx]

        speak(f"Reading email subject {selected['subject']}")
        snippet = selected["raw"].get("snippet")
        if snippet:
            speak(snippet)

        ask_and_handle_reply(service, selected)

    # 🗑 DELETE EMAIL FROM SENDER
    elif intent["intent"] == "DELETE_EMAIL_FROM_SENDER":
        shared_state.current_action = "deleting email"
        sender_name = intent.get("to")
        sender_email = resolve_contact(sender_name) or sender_name

        emails = get_emails_from_sender(service, sender_email)

        if not emails:
            speak(f"No recent emails from {sender_name}")
            return True

        speak(f"here are the last {len(emails)} emails from {sender_name}")

        for i, mail in enumerate(emails, start=1):
            speak(f"Email {i}: {mail['subject']}")

        speak("Which email should I delete? Say one, two, or three.")
        path=app_path("audio","choice.wav")
        ensure_audio_path(path)
        record_audio(path)
        choice_text = transcribe(path)

        idx = pick_index(choice_text)
        if idx is None or idx >= len(emails):
            speak("Invalid choice")
            return True

        selected = emails[idx]

        speak(f"Are you sure you want to delete the email with subject {selected['subject']}?")
        path=app_path("audio","confirm.wav")
        ensure_audio_path(path)
        record_audio(path)
        confirm = transcribe(path)

        if is_positive(confirm):
            delete_email(service, selected["id"])
            speak("Email moved to trash")
        else:
            speak("Deletion cancelled")

    # 📝 SUMMARIZE EMAIL
    elif intent["intent"] == "SUMMARIZE_LATEST_EMAIL":
        email = get_latest_email(service)
        if not email:
            speak("No email to summarize")
        else:
            speak(f"Latest email subject is {email['subject']}")

    # 🧹 DELETE ALL READ EMAILS
    elif intent["intent"] == "DELETE_LATEST_EMAIL" and "read" in text.lower():
        shared_state.current_action = "deleting email"
        speak("This will move all read emails to trash. Are you sure?")
        path=app_path("audio","confirm.wav")
        ensure_audio_path(path)
        record_audio(path)
        confirm = transcribe(path)

        if not is_positive(confirm):
            speak("Cancelled")
            return True

        from gmail.gmail_client import get_read_emails
        read_emails = get_read_emails(service)

        if not read_emails:
            speak("There are no read emails to delete")
            return True

        for msg in read_emails:
            delete_email(service, msg["id"])

        speak(f"Moved {len(read_emails)} read emails to trash")

    # 🗑 DELETE LATEST EMAIL
    elif intent["intent"] == "DELETE_LATEST_EMAIL":
        shared_state.current_action = "deleting email"
        email = get_latest_email(service)
        if not email:
            speak("No email to delete")
            return True

        speak(f"Email from {email['from']}")
        speak(f"Subject {email['subject']}")
        speak("Are you sure you want to delete this email?")

        path=app_path("audio","confirm.wav")
        ensure_audio_path(path)
        record_audio(path)
        reply = transcribe(path)

        if is_positive(reply):
            delete_email(service, email["id"])
            speak("Email moved to trash")
        else:
            speak("Deletion cancelled")

    elif intent["intent"] == "CANCEL":
        speak("Okay. Going back to sleep.")
        return False

    else:
        speak("Sorry, I did not understand")

    speak("Anything else?")
    return True


def main():
    speak("Assistant is loaded. Say the wake word to start.")
    service = authenticate_gmail()
    shared_state.current_action = "email authentication"

    while True:
        shared_state.assistant_state = "sleeping"

        path=app_path("audio","wake.wav")
        ensure_audio_path(path)
        record_audio(path)
        heard = transcribe(path)

        print("Wake heard:", heard)


        if is_shutdown(heard):
            speak("Goodbye. Shutting down.")
            sys.exit(0)

        if is_wake_word(heard):
            speak("Yes, I am listening")
            shared_state.assistant_state = "listening"


            misunderstand_count = 0

            while True:
                result = handle_command(service)

                if not result:
                    break

                misunderstand_count += 1
                if misunderstand_count >= 5:
                    speak("I am going back to sleep.")
                    shared_state.assistant_state = "sleeping"
                    shared_state.current_action = ""

                    break

        time.sleep(0.4)


if __name__ == "__main__":
    main()
