from audio.recorder import record_audio
from stt.whisper_engine import transcribe
from llm.intent_engine import extract_intent
from llm.intent_utils import normalize_intent
from gmail.gmail_client import (
    authenticate_gmail,
    send_email,
    get_latest_email,
    delete_email,
)
from tts.speaker import speak
from utils.email_analyzer import analyze_email, html_to_text
import time


WAKE_WORDS = ["hey assistant", "hello assistant"]
EXIT_WORDS = ["cancel", "stop", "go to sleep", "sleep"]


def is_wake_word(text: str) -> bool:
    text = text.lower()
    return any(wake in text for wake in WAKE_WORDS)


def is_exit(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in EXIT_WORDS)


def is_positive(text: str) -> bool:
    text = text.lower()
    return any(
        word in text
        for word in ["yes", "yeah", "sure", "ok", "okay", "read", "delete"]
    )


def handle_command(service) -> bool:
    """
    Returns False if session should end
    """
    record_audio("audio/input.wav")
    text = transcribe("audio/input.wav")

    print("You said:", text)

    if is_exit(text):
        speak("Okay. Going back to sleep.")
        return False

    intent_raw = extract_intent(text)
    intent = normalize_intent(intent_raw)

    print("Intent:", intent)

    # SEND EMAIL
    if intent["intent"] == "SEND_EMAIL":
        if not intent["to"] or not intent["body"]:
            speak("I need a recipient and message")
            return True

        speak(f"Sending email to {intent['to']}")
        send_email(
            service,
            to_email=intent["to"],
            subject=intent["subject"] or "Voice Assistant Message",
            body=intent["body"],
        )
        speak("Email sent")

    # READ EMAIL
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

    # SUMMARIZE EMAIL
    elif intent["intent"] == "SUMMARIZE_LATEST_EMAIL":
        email = get_latest_email(service)
        if not email:
            speak("No email to summarize")
        else:
            speak(f"Latest email subject is {email['subject']}")

    # DELETE EMAIL
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
    speak("Assistant is loaded. Say hey assistant to wake me up.")
    service = authenticate_gmail()

    while True:
        # Wake word listening
        record_audio("audio/wake.wav")
        heard = transcribe("audio/wake.wav")

        print("Wake heard:", heard)

        if is_wake_word(heard):
            speak("Yes, I am listening")

            session_active = True
            misunderstand_count = 0

            while session_active:
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
