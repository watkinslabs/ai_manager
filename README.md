# AI Manager Module

Python module providing unified access to OpenAI's chat, text-to-speech, and transcription APIs.

## Features

- **Chat completions** with prompt template support
- **Text-to-speech** generation (WAV output)
- **Audio transcription** using Whisper
- **Template-based prompts** from filesystem
- **Comprehensive logging**

## Installation

```bash
dnf install python3-pip
pip install openai soundfile
```

## Quick Start

```python
from ai_manager import AIManager

# Initialize with config object
ai = AIManager(config)

# Chat completion
response = ai.chat("my_prompt", {"name": "John"})

# Generate speech
ai.generate_speech("Hello world", output_path="output.wav")

# Transcribe audio
text = ai.transcribe_audio(audio_path="input.wav")
```

## Configuration

Config object needs:
- `openai.api_key`
- `openai.organization_id`  
- `openai.chat_model`
- `openai.tts_voice`/`tts_model`
- `prompt_folder`
- `output_dir`

## Prompt Templates

Store `.txt` files in configured prompt folder:
- `prompt_name.txt` - Simple prompt
- `prompt_name.system.txt` + `prompt_name.user.txt` - System/user pair

Use `{variable}` placeholders for data substitution.

## License

BSD 3-Clause