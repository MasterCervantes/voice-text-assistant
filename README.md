# Voice-Enabled Text Assistant

A voice-enabled chat interface for Ollama models with text-to-speech capabilities.

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Platform-specific requirements:

### Windows
No additional setup needed - uses SAPI5

### Linux
Install espeak:
```bash
sudo apt-get install espeak
```

### macOS
No additional setup needed - uses NSSpeechSynthesizer

## Usage

1. Start Ollama server
2. Run the assistant:
```bash
python VoiceTextAssistant.py
```

## Features

- Text-to-speech output for AI responses
- Voice selection
- Adjustable speech rate and volume
- Conversation history
- Save/load conversations
- Custom save location