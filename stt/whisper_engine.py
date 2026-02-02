import whisper

_model = None

def load_model():
    global _model
    if _model is None:
        print("Loading Whisper BASE model...")
        _model = whisper.load_model(
            "tiny",
            device="cpu"   # force CPU, avoids slow checks
        )
    return _model

def transcribe(audio_file):
    model = load_model()
    result = model.transcribe(
        audio_file,
        language="en",
        fp16=False,                         # CPU speedup
        condition_on_previous_text=False   # BIG speed win
    )
    return result["text"].strip()
