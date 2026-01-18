import ollama


def extract_intent(text: str) -> dict:
    try:
        response = ollama.generate(
            model="phi3:mini",
            prompt=f"""
Extract intent from the following voice command.

Allowed intents:
- SEND_EMAIL
- READ_LATEST_EMAIL
- SUMMARIZE_LATEST_EMAIL
- DELETE_LATEST_EMAIL
- CANCEL

Voice command:
{text}

Return JSON with exactly these fields:
intent, to, subject, body
""",
            format="json",          # 🔑 THIS IS THE FIX
            options={
                "temperature": 0,
                "num_predict": 150
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
