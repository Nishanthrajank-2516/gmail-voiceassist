import ollama


def extract_intent(text: str) -> dict:
    try:
        response = ollama.generate(
            model="phi3:mini",
            prompt=f"""
You are an intent extraction engine.

Allowed intents:
- SEND_EMAIL
- READ_LATEST_EMAIL
- READ_EMAIL_FROM_SENDER
- READ_UNREAD_EMAILS
- SUMMARIZE_LATEST_EMAIL
- DELETE_LATEST_EMAIL
- DELETE_EMAIL_FROM_SENDER
- CANCEL

Rules:
- If the user says "unread", "list unread", or "unread emails", use READ_UNREAD_EMAILS
- If the user says "read mail from X" or "emails from X", use READ_EMAIL_FROM_SENDER and set "to" = X
- If the user says "delete mail from X" or "remove emails from X", use DELETE_EMAIL_FROM_SENDER and set "to" = X
- If the user says "delete mail" with no sender, use DELETE_LATEST_EMAIL
- If no sender or unread keyword is mentioned, use READ_LATEST_EMAIL

Voice command:
{text}

Return ONLY valid JSON with exactly these fields:
intent, to, subject, body
""",
            format="json",
            options={
                "temperature": 0,
                "num_predict": 120
            }
        )

        return response["response"]

    except Exception as e:
        print("LLM ERROR:", e)
        return {
            "intent": "UNKNOWN",
            "to": None,
            "subject": None,
            "body": None
        }
