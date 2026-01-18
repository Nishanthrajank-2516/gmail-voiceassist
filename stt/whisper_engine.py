# placeholder
import whisper

_model = None

def load_model():
    global _model
    if _model is None:
        print("Loading Whisper BASE model...")
        _model = whisper.load_model("base")
    return _model

def transcribe(audio_file):
    model = load_model()
    result = model.transcribe(audio_file, language="en")
    return result["text"].strip()
