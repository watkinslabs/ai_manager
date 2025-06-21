# AI Manager

A general-purpose Python toolkit for commonly performed AI tasks, providing a unified interface for OpenAI and Replicate APIs.

## Features

- **Chat Completions** - Generate text with OpenAI models, including schema validation
- **Text-to-Speech** - Convert text to speech using OpenAI's TTS
- **Speech-to-Text** - Transcribe audio using OpenAI's Whisper
- **Image Generation** - Create images using FLUX PRO via Replicate
- **Video Generation** - Generate videos using Google's VEO-2 via Replicate
- **Music Generation** - Create music tracks with continuation and variations
- **Prompt Management** - Load and manage prompts from files
- **Schema Validation** - Validate AI responses against JSON schemas

## Installation

```bash
pip install wl-ai-manager
```

## Dependencies

- `wl_config_manager`
- `wl_version_manager`
- `openai`
- `replicate`
- `pillow`
- `soundfile`
- `jsonschema`
- `pyyaml`
- `requests`

## Configuration

Create a YAML configuration file with the `ai_manager` root element:

```yaml
ai_manager:
  output_dir: "./output"
  temp_dir: "/tmp"
  prompt_folder: "./prompts"
  schema_folder: "./schemas"
  max_validation_retries: 3
  
  openai:
    api_key: "your-openai-api-key"
    organization_id: "your-org-id"
    chat_model: "gpt-4"
    tts_model: "tts-1"
    tts_voice: "nova"
    whisper_model: "whisper-1"
  
  replicate:
    api_key: "your-replicate-api-key"
    image_model: "black-forest-labs/flux-pro"
    video_model: "google/veo-2"
    music_model: "meta/musicgen"
    prompt_upsampling: true
    output_format: "png"
    num_inference_steps: 50
    guidance_scale: 7.5
```

## Usage

### Initialize AI Manager

```python
from wl_config_manager import ConfigManager
from wl_ai_manager import AIManager

# Load configuration
config = ConfigManager("config.yaml")
ai_manager = AIManager(config.ai_manager)
```

### Chat Completions

```python
# Simple chat
response = ai_manager.chat(
    prompt_name="analyze_text",
    data={"text": "Hello world"},
    model="gpt-4"  # Optional, uses config default
)

# Chat with schema validation
validated_response = ai_manager.chat(
    prompt_name="extract_entities",
    data={"text": "John lives in New York"},
    validate=True  # Enables automatic retry with schema validation
)
```

### Text-to-Speech

```python
# Generate speech from text
audio_path = ai_manager.generate_speech(
    text="Hello, this is a test",
    voice="nova",  # Optional, uses config default
    output_path="./output/speech.wav"
)
```

### Speech-to-Text

```python
# Transcribe audio file
transcript = ai_manager.transcribe_audio(
    audio_path="./audio/recording.wav"
)

# Transcribe audio data (numpy array or bytes)
transcript = ai_manager.transcribe_audio(
    audio_data=audio_array
)
```

### Image Generation

```python
# Generate image with FLUX PRO
image_path = ai_manager.generate_image(
    prompt="A beautiful sunset over mountains",
    file_name="sunset",
    file_type="png",
    width=1024,
    height=768,
    resize=True,  # Resize to exact dimensions
    crop=False    # Crop to exact dimensions
)
```

### Video Generation

```python
# Generate video from text prompt
video_path = ai_manager.generate_video(
    prompt="A cat playing with a ball of yarn",
    duration=10,  # 5, 10, 15, or 20 seconds
    aspect_ratio="16:9"  # "16:9", "9:16", "1:1", "4:3", "3:4"
)

# Generate video from image (when supported)
video_path = ai_manager.generate_video_from_image(
    image_path="./images/cat.jpg",
    prompt="Make the cat move and play",
    duration=5
)
```

### Music Generation

```python
# Generate single music track
music_path = ai_manager.generate_music(
    prompt="Upbeat electronic dance music with synth",
    duration=30,
    temperature=1.0,
    output_format="wav"
)

# Generate music with continuation
music_path = ai_manager.generate_music(
    prompt="Continue this melody with strings",
    continuation_audio="./music/intro.wav",
    duration=30
)

# Generate music chain (each continues from previous)
music_files = ai_manager.generate_music_chain(
    prompts=[
        "Gentle piano intro",
        "Add strings and build intensity",
        "Climax with full orchestra",
        "Gentle outro"
    ],
    duration=30  # per segment
)

# Generate variations of a theme
variations = ai_manager.generate_music_variations(
    base_prompt="Classical piano melody",
    variations=[
        "in minor key",
        "with jazz influences",
        "as a waltz",
        "with electronic elements"
    ],
    duration=30
)
```

## Prompt Management

Create prompt files in your configured `prompt_folder`:

### Standard Prompt (`analyze.txt`)
```
Analyze the following text: {text}
```

### System/User Prompt Pair
`summarize.system.txt`:
```
You are a professional summarizer.
```

`summarize.user.txt`:
```
Summarize this document: {document}
```

### Using Prompts
```python
# The prompt name matches the filename without extension
response = ai_manager.chat(
    prompt_name="analyze",
    data={"text": "Some text to analyze"}
)
```

## Schema Validation

Create schema example files in your `schema_folder` with `.schema.txt` extension:

`extract_entities.schema.txt`:
```json
{
  "entities": [
    {
      "name": "string",
      "type": "person|place|organization",
      "confidence": 0.95
    }
  ],
  "relationships": []
}
```

### Using Schema Validation
```python
# Automatic validation with retries
result = ai_manager.chat(
    prompt_name="extract_entities",
    data={"text": "Apple Inc. is located in Cupertino"},
    validate=True
)

# result will be the parsed JSON/YAML data, not raw text
print(result["entities"])  # [{"name": "Apple Inc.", "type": "organization", ...}]
```

### Manual Validation
```python
# Check if schema exists
if ai_manager.has_schema_for_prompt("extract_entities"):
    # Validate arbitrary response
    validation = ai_manager.validate_response_for_prompt(
        response='{"entities": [...]}',
        prompt_name="extract_entities"
    )
    if validation["valid"]:
        data = validation["data"]
```

## Advanced Features

### Get Available Prompts and Schemas
```python
# List all loaded prompts
prompts = ai_manager.get_prompts()

# List prompts with schemas
schema_prompts = ai_manager.get_schema_prompts()

# List all available schemas
schemas = ai_manager.get_available_schemas()
```

### Custom Schema Validation
```python
# Add schema programmatically
ai_manager.add_schema("custom_format", {
    "type": "object",
    "properties": {
        "result": {"type": "string"},
        "confidence": {"type": "number"}
    },
    "required": ["result"]
})

# Validate data against custom schema
validation = ai_manager.validate_data(
    data={"result": "success", "confidence": 0.9},
    schema_name="custom_format"
)
```

## Error Handling

All methods return `None` or error dictionaries on failure:

```python
# Check for failures
response = ai_manager.chat("my_prompt", data={})
if response is None:
    print("Chat generation failed")

# With validation, errors are returned as dict
result = ai_manager.chat("extract", data={}, validate=True)
if isinstance(result, dict) and "error" in result:
    print(f"Validation failed: {result['error']}")
    print(f"After {result['attempts']} attempts")
```

## Best Practices

1. **Configuration**: Store API keys in environment variables and load them in your YAML config
2. **Prompts**: Use descriptive filenames for prompts (e.g., `analyze_sentiment.txt`)
3. **Schemas**: Provide clear example structures in `.schema.txt` files
4. **Error Handling**: Always check return values for `None` or error dictionaries
5. **Resource Management**: The manager handles file operations and API clients internally

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.