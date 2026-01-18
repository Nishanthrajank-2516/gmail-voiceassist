def is_positive(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in ["yes", "yeah", "sure", "ok", "okay", "read"])
