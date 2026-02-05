# Voice Gmail Assistant

A voice-activated AI assistant designed to manage your Gmail inbox hands-free. This application leverages local LLMs for intent recognition and email refinement, OpenAI Whisper for privacy-focused speech-to-text, and Piper for natural-sounding text-to-speech.

## Features

-   **Voice Activation**: Listens for wake words (e.g., "Zara", "Sara") to start interaction.
-   **Smart Email Management**:
    -   **Read Emails**: List and read unread emails or emails from specific senders.
    -   **Send & Reply**: Compose and send emails using voice dictation. The assistant automatically refines your spoken drafts for grammar and clarity.
    -   **Forward**: Easy voice commands to forward emails to contacts.
    -   **Delete**: Move emails to trash with voice confirmation.
-   **Local Intelligence**:
    -   Uses local LLMs (e.g., via Ollama/LlamaCPP) for understanding user intent and summarizing content.
    -   Privacy-first design with local processing where possible.
-   **Web Dashboard**: A visual interface that displays the assistant's current state (Listening, Speaking, Processing) and transcripts of interactions.

## Prerequisites

Before running the application, ensure you have the following installed:

-   **Python 3.10+**
-   **System Dependencies** (Linux):
    ```bash
    sudo apt-get install python3-dev portaudio19-dev libsndfile1 ffmpeg
    ```
    *Note: `portaudio` is required for microphone access, and `ffmpeg` is used for audio processing.*

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd gmail-voice-assistant
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Google Cloud Credentials**:
    -   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    -   Create a new project and enable the **Gmail API**.
    -   Create OAuth 2.0 Desktop credentials.
    -   Download the JSON file and save it as `credentials.json` in the `config/` directory.

2.  **Local LLM Setup**:
    -   Ensure you have the required models downloaded for `llama_cpp_python` or `ollama` as configured in your `llm` module.
    -   (Optional) Check `config/settings.py` to adjust wake words, recording duration, or model paths.

## Usage

1.  **Start the Assistant**:
    ```bash
    python main.py
    ```

2.  **Authorize Gmail**:
    -   On the first run, a browser window will open asking for permission to access your Gmail account.
    -   Look for `config/token.json` to be confirmed created after successful login.

3.  **Interact**:
    -   **Wake**: Say "Zara" or "Sara".
    -   **Command Examples**:
        -   *"Read my unread emails"*
        -   *"Send an email to John about the meeting"*
        -   *"Delete the last email"*
        -   *"Read the latest email from Amazon"*

4.  **Web Interface**:
    -   The dashboard automatically launches at `http://127.0.0.1:5000`.

## License

[MIT License](LICENSE)
