from audio.recorder import record_audio
from stt.whisper_engine import transcribe
from utils.contacts import resolve_contact

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
import sys


# 🔊 Wake words
WAKE_WORDS = ["zara", "sara"]

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
        for word in ["yes", "yeah", "sure", "ok", "okay", "read", "delete", "reply"]
    )


def pick_index(text: str) -> int | None:
    mapping = {
        "one": 0,
        "two": 1,
        "three": 2,
        "1": 0,
        "2": 1,
        "3": 2,
    }
    return mapping.get(text.lower())


def ask_and_handle_reply(service, email_obj):
    speak("Do you want to reply to this email?")
    record_audio("audio/reply_confirm.wav")
    reply = transcribe("audio/reply_confirm.wav")

    if is_positive(reply):
        speak("What should I reply?")
        record_audio("audio/reply_body.wav")
        reply_text = transcribe("audio/reply_body.wav")

        reply_to_email(service, email_obj, reply_text)
        speak("Reply sent")


def handle_command(service) -> bool:
    record_audio("audio/input.wav")
    text = transcribe("audio/input.wav")

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

    # 🟡 NEW: sender-aware upgrade (NO feature removal)
    if intent["intent"] == "READ_LATEST_EMAIL" and intent.get("to"):
        intent["intent"] = "READ_EMAIL_FROM_SENDER"

    # 📧 SEND EMAIL
    if intent["intent"] == "SEND_EMAIL":
        if not intent["to"] or not intent["body"]:
            speak("I need a recipient and message")
            return True

        resolved_email = resolve_contact(intent["to"]) or intent["to"]

        speak(f"Sending email to {intent['to']}")
        send_email(
            service,
            to_email=resolved_email,
            subject=intent["subject"] or "Voice Assistant Message",
            body=intent["body"],
        )
        speak("Email sent")

    # 📖 READ LATEST EMAIL (unchanged)
    elif intent["intent"] == "READ_LATEST_EMAIL":
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
        record_audio("audio/confirm.wav")
        reply = transcribe("audio/confirm.wav")

        if is_positive(reply):
            if email.get("body"):
                speak(email["body"])
            elif email.get("html"):
                speak("Reading extracted text from HTML email")
                speak(html_to_text(email["html"]))
            else:
                speak("This email does not contain readable text")

            ask_and_handle_reply(service, email)

    # 📬 READ EMAILS FROM SENDER (unchanged, now reachable)
    elif intent["intent"] == "READ_EMAIL_FROM_SENDER":
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
        record_audio("audio/choice.wav")
        choice_text = transcribe("audio/choice.wav")

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

    # 📝 SUMMARIZE EMAIL
    elif intent["intent"] == "SUMMARIZE_LATEST_EMAIL":
        email = get_latest_email(service)
        if not email:
            speak("No email to summarize")
        else:
            speak(f"Latest email subject is {email['subject']}")

    # 🗑 DELETE EMAIL
    elif intent["intent"] == "DELETE_LATEST_EMAIL":
        email = get_latest_email(service)
        if not email:
            speak("No email to delete")
            return True

        speak(f"Email from {email['from']}")
        speak(f"Subject {email['subject']}")
        speak("Are you sure you want to delete this email?")

        record_audio("audio/confirm.wav")
        reply = transcribe("audio/confirm.wav")

        if is_positive(reply):
            delete_email(service, email["id"])
            speak("Email deleted")
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
    speak("Assistant is running. Say the wake word to wake me up.")
    service = authenticate_gmail()

    while True:
        record_audio("audio/wake.wav")
        heard = transcribe("audio/wake.wav")

        print("Wake heard:", heard)

        # 🛑 Shutdown from wake state
        if is_shutdown(heard):
            speak("Goodbye. Shutting down.")
            sys.exit(0)

        if is_wake_word(heard):
            speak("Yes, I am listening")

            misunderstand_count = 0

            while True:
                result = handle_command(service)

                if not result:
                    break

                misunderstand_count += 1
                if misunderstand_count >= 2:
                    speak("I am going back to sleep.")
                    break

        time.sleep(0.4)


if __name__ == "__main__":
    main()
