import ollama

def extract_intent(text: str) -> dict:
    prompt = f"""
Extract intent from the command.

Valid intents:
SEND_EMAIL
READ_LATEST_EMAIL
READ_EMAIL_FROM_SENDER
READ_UNREAD_EMAILS
DELETE_LATEST_EMAIL
DELETE_EMAIL_FROM_SENDER
SUMMARIZE_LATEST_EMAIL
CANCEL

Command:
{text}

Return JSON only:
{{"intent": "", "to": null}}
"""

    try:
        res = ollama.generate(
            model="phi3:mini",
            prompt=prompt,
            format="json",
            options={
                "temperature": 0,
                "num_predict": 60
            }
        )
        return res["response"]

    except Exception as e:
        print("LLM ERROR:", e)
        return {
            "intent": "UNKNOWN",
            "to": None
        }
