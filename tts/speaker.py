import subprocess

def speak(text: str):
    subprocess.run(
        ["festival", "--tts"],
        input=text.encode("utf-8"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
