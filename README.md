# AI Manager

Python module providing unified access to OpenAI's chat, text-to-speech, and transcription APIs with template-based prompt management.

## Features

- **Chat Completions** - Generate responses using OpenAI's chat models
- **Text-to-Speech** - Convert text to audio using OpenAI's TTS API
- **Audio Transcription** - Transcribe audio files using Whisper
- **Template System** - File-based prompt templates with variable substitution
- **Comprehensive Logging** - Built-in logging for debugging and monitoring

## Installation

### Prerequisites (Fedora/CentOS)

```bash
dnf install python3-pip pipenv
```

### Install from PyPI

```bash
pip install ai_manager
```

### Install from Source

```bash
git clone https://github.com/watkinslabs/ai_manager.git
cd ai_manager
make setup-dev
```

## Quick Start

```python
from ai_manager import AIManager

# Initialize with configuration
ai = AIManager(config)

# Chat completion
response = ai.chat("greeting", {"name": "John"})
print(response)

# Generate speech
speech_path = ai.generate_speech("Hello world!", output_path="hello.wav")

# Transcribe audio
text = ai.transcribe_audio(audio_path="recording.wav")
print(text)
```

## Configuration

Your config object must include:

```python
class Config:
    class openai:
        api_key = "sk-..."
        organization_id = "org-..."
        chat_model = "gpt-4"
        tts_voice = "alloy"
        tts_model = "tts-1"
        whisper_model = "whisper-1"
    
    prompt_folder = "/path/to/prompts"
    output_dir = "/path/to/output"
    temp_dir = "/tmp"
    sample_rate = 44100
```

## Prompt Templates

Create `.txt` files in your prompt folder:

### Simple Prompts
```
# prompts/greeting.txt
Hello {name}! How can I help you today?
```

### System/User Prompts
```
# prompts/assistant.system.txt
You are a helpful AI assistant.

# prompts/assistant.user.txt
Please help me with: {task}
```

Use `{variable}` placeholders for dynamic content.

## API Reference

### AIManager Class

#### `__init__(config)`
Initialize AI Manager with configuration object.

#### `chat(prompt_name, data={}, model=None)`
Generate chat completion using template.

**Parameters:**
- `prompt_name` - Name of prompt template
- `data` - Dictionary for variable substitution
- `model` - Override default chat model

**Returns:** Generated text or None on failure

#### `generate_speech(text, voice=None, model=None, output_path=None)`
Convert text to speech.

**Parameters:**
- `text` - Text to convert
- `voice` - Voice to use (defaults to config)
- `model` - TTS model (defaults to config)
- `output_path` - Output WAV file path

**Returns:** Output path or None on failure

#### `transcribe_audio(audio_data=None, audio_path=None)`
Transcribe audio using Whisper.

**Parameters:**
- `audio_data` - Raw audio data or numpy array
- `audio_path` - Path to audio file

**Returns:** Transcribed text or None on failure

### Standalone Functions

```python
from ai_manager import chat, generate_speech, transcribe_audio

# Direct function calls
text = chat("prompt_name", {"key": "value"}, model, client, prompts)
path = generate_speech("Hello", "alloy", "tts-1", "out.wav", client)
result = transcribe_audio(audio_data=data, client=client)
```

## Development

### Setup Development Environment

```bash
make setup-dev
```

### Available Make Targets

```bash
make help           # Show all targets
make build          # Build distribution packages
make test           # Run tests
make lint           # Run linting
make format         # Format code with black
make install        # Install with pipenv
make uninstall      # Remove from pipenv
make upload-test    # Upload to TestPyPI
make upload-prod    # Upload to PyPI
```

### Running Tests

```bash
make test
```

### Code Formatting

```bash
make format
make lint
```

## Examples

### Basic Chat

```python
from ai_manager import AIManager

ai = AIManager(config)

# Simple prompt
response = ai.chat("summarize", {
    "text": "Long article content here..."
})

# System/user prompt
response = ai.chat("code_review", {
    "language": "python",
    "code": "def hello(): pass"
})
```

### Text-to-Speech Pipeline

```python
# Generate speech with custom settings
speech_file = ai.generate_speech(
    text="Welcome to our application!",
    voice="nova",
    model="tts-1-hd",
    output_path="welcome.wav"
)

if speech_file:
    print(f"Speech saved to: {speech_file}")
```

### Audio Transcription

```python
# Transcribe from file
transcript = ai.transcribe_audio(audio_path="meeting.wav")

# Transcribe from raw data
with open("audio.wav", "rb") as f:
    audio_data = f.read()
    transcript = ai.transcribe_audio(audio_data=audio_data)
```

## Error Handling

All methods return `None` on failure and log errors. Always check return values:

```python
response = ai.chat("prompt", data)
if response is None:
    print("Chat generation failed")
    
speech_path = ai.generate_speech("text")
if speech_path is None:
    print("Speech generation failed")
```

## Logging

Enable logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## License

BSD 3-Clause License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `make pre-upload` to verify
5. Submit a pull request

## Support

- Issues: GitHub Issues
- Documentation: This README
- Examples: See examples/ directory