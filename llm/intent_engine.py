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
- SUMMARIZE_LATEST_EMAIL
- DELETE_LATEST_EMAIL
- CANCEL

Rules:
- If the user says "read mail from X" or "emails from X", use READ_EMAIL_FROM_SENDER and set "to" as X
- If no sender is mentioned, use READ_LATEST_EMAIL

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
