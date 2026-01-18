import json


def normalize_intent(data):
    # If Ollama returned JSON as string, parse it
    if isinstance(data, str):
        data = json.loads(data)

    def clean(value):
        if value is None:
            return None
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    return {
        "intent": clean(data.get("intent")),
        "to": clean(data.get("to")),
        "subject": clean(data.get("subject")),
        "body": clean(data.get("body")),
    }
