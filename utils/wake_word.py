WAKE_WORDS = [
    "hey assistant",
    "hello assistant"
]

def is_wake_word(text: str) -> bool:
    text = text.lower()
    return any(wake in text for wake in WAKE_WORDS)
