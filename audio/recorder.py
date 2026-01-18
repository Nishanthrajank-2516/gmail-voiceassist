import sounddevice as sd
import scipy.io.wavfile as wav
from config.settings import SAMPLE_RATE, RECORD_SECONDS

def record_audio(output_file):
    print("Recording... Speak now.")
    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()
    print("Recording finished.")
    wav.write(output_file, SAMPLE_RATE, audio)
