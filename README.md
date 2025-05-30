# AI Manager

A comprehensive Python wrapper for OpenAI's APIs, providing chat completions, text-to-speech, transcription, and structured response validation with automatic retry logic.

## Features

- **Chat Completions**: Clean interface for OpenAI's chat API with template-based prompts
- **Schema Validation**: Automatic JSON/YAML validation with configurable retry logic
- **Text-to-Speech**: Generate speech from text with customizable voices
- **Transcription**: Convert audio to text using Whisper API
- **Template System**: Flexible prompt management with system/user message support
- **Error Handling**: Robust error handling with detailed logging

## Installation

```bash
pip install openai jsonschema pyyaml soundfile wl-config-manager
```

## Quick Start

### 1. Configuration

Create a YAML configuration file:

```yaml
# config.yaml

# OpenAI API settings
openai:
  api_key: "${OPENAI_API_KEY}"
  organization_id: "${OPENAI_ORG_ID}"
  chat_model: "gpt-4o-mini"
  tts_model: "tts-1"
  tts_voice: "alloy"
  whisper_model: "whisper-1"

# Directory paths
prompt_folder: "prompts"
schema_folder: "schemas"
output_dir: "output"
temp_dir: "/tmp"

# Validation settings
max_validation_retries: 3
sample_rate: 44100

# Custom template (optional)
schema_prompt_template: |
  {base_prompt}

  Return response in JSON or YAML format following this example:
  {schema_content}

  Respond with only structured data, no additional text.
```

```python
from wl_config_manager import ConfigManager
from ai_manager import AIManager

# Load configuration
config_manager = ConfigManager("config.yaml")
ai_manager = AIManager(config_manager.config)
```

### 2. Basic Chat

```python
# Simple chat
response = ai_manager.chat('get_weather', {'city': 'Boston'})
print(response)  # "The weather in Boston is sunny with 75°F"
```

### 3. Structured Responses with Validation

```python
# Chat with automatic validation and retry
user_data = ai_manager.chat('create_user', {
    'name': 'Alice',
    'email': 'alice@example.com'
}, validate=True)

print(user_data)  # {'id': 123, 'name': 'Alice', 'email': 'alice@example.com', 'active': True}
```

## File Structure

```
your_project/
├── prompts/
│   ├── get_weather.txt              # Regular prompt
│   ├── create_user.txt              # Structured prompt
│   ├── complex_task.system.txt      # System message
│   └── complex_task.user.txt        # User message
├── schemas/
│   ├── create_user.schema.txt       # JSON/YAML example for create_user.txt
│   └── complex_task.schema.txt      # Schema for complex_task
└── output/
    └── speech/                      # Generated speech files
```

## Prompt Files

### Regular Prompt (`prompts/get_weather.txt`)
```
Get the current weather for {city}. Include temperature, conditions, and any weather alerts.
```

### Structured Prompt (`prompts/create_user.txt`)
```
Create a new user account with the following details:
- Name: {name}
- Email: {email} 
- Role: {role}
```

### System/User Prompts
```
# prompts/analyze_data.system.txt
You are a expert data analyst. Provide clear, actionable insights.

# prompts/analyze_data.user.txt  
Analyze this dataset: {data}
Focus on trends, anomalies, and recommendations.
```

## Schema Files

Schema files provide examples of the expected output format for structured prompts.

### JSON Schema (`schemas/create_user.schema.txt`)
```json
{
  "id": 12345,
  "name": "John Doe",
  "email": "john@example.com", 
  "role": "user",
  "active": true,
  "created_at": "2025-05-30T12:00:00Z"
}
```

### YAML Schema (`schemas/analyze_data.schema.txt`)
```yaml
analysis:
  summary: "Data shows positive trend over 6 months"
  metrics:
    - name: "average_value"
      value: 42.5
    - name: "total_records"
      value: 1250
  insights:
    - "Key finding 1"
    - "Recommendation 2" 
  confidence: 0.85
```

## API Reference

### AIManager.chat()

```python
def chat(self, prompt_name, data={}, model=None, validate=False):
    """
    Generate chat completion with optional validation.
    
    Args:
        prompt_name (str): Name of prompt file (without .txt)
        data (dict): Variables to format into prompt template
        model (str): OpenAI model to use (optional)
        validate (bool): Enable structured response validation
        
    Returns:
        str|dict: Raw text response or parsed structured data
        
    Raises:
        None: Returns error dict on failure when validate=True
    """
```

**Examples:**

```python
# Basic usage
response = ai_manager.chat('greeting', {'name': 'Alice'})

# With validation
user = ai_manager.chat('create_user', {
    'name': 'Bob', 
    'email': 'bob@test.com',
    'role': 'admin'
}, validate=True)

# Custom model
analysis = ai_manager.chat('analyze_data', 
    {'data': 'sales_q1.csv'}, 
    model='gpt-4o',
    validate=True
)
```

### Other Methods

```python
# Text-to-speech
ai_manager.generate_speech("Hello world", output_path="/path/to/speech.wav")

# Transcription  
text = ai_manager.transcribe_audio(audio_path="/path/to/audio.wav")

# Get prompts with schemas
schema_prompts = ai_manager.get_schema_prompts()

# Check if prompt has schema
if ai_manager.has_schema_for_prompt('create_user'):
    # Validation available
    pass
```

## Validation and Retry Logic

When `validate=True`:

1. **Prompt Enhancement**: Automatically combines your prompt with schema example
2. **Response Sanitization**: Removes common LLM wrapper text ("Here's the JSON:", code blocks, etc.)
3. **Format Detection**: Attempts to parse as JSON first, then YAML
4. **Automatic Retry**: Retries up to `max_validation_retries` times on parsing failure
5. **Structured Return**: Returns parsed data on success, detailed error info on failure

### Success Response
```python
{
    "id": 123,
    "name": "Alice", 
    "email": "alice@example.com",
    "active": True
}
```

### Failure Response
```python
{
    "error": "Validation failed after all retries",
    "attempts": 3,
    "last_response": "The raw LLM response text",
    "validation_result": {
        "valid": False,
        "errors": ["JSON error: ...", "YAML error: ..."],
        "sanitized_response": "cleaned response"
    },
    "prompt_name": "create_user"
}
```

## Configuration Options

All configuration is done via YAML file loaded with WL_CONFIG_MANAGER:

```yaml
# Required OpenAI settings
openai:
  api_key: "${OPENAI_API_KEY}"           # API key (use env var)
  organization_id: "${OPENAI_ORG_ID}"    # Organization ID (optional)
  chat_model: "gpt-4o-mini"              # Chat completion model
  tts_model: "tts-1"                     # Text-to-speech model
  tts_voice: "alloy"                     # TTS voice
  whisper_model: "whisper-1"             # Transcription model

# Required directory paths
prompt_folder: "prompts"                 # Prompt files directory
schema_folder: "schemas"                 # Schema files directory (optional)

# Optional settings
output_dir: "output"                     # Output files directory
temp_dir: "/tmp"                         # Temporary files
max_validation_retries: 3                # Retry attempts for validation
sample_rate: 44100                       # Audio sample rate

# Custom template for combining prompts with schemas (optional)
schema_prompt_template: |
  {base_prompt}

  Return response in JSON or YAML format following this example:
  {schema_content}

  Respond with only structured data, no additional text.
```

### Environment Variables

Set your OpenAI credentials:

```bash
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_ORG_ID="your-org-id-here"  # Optional
```

## Error Handling

The AI Manager uses Python's `logging` module for comprehensive error tracking:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Enable debug logging for detailed info
logging.getLogger('ai_manager').setLevel(logging.DEBUG)
```

Common error scenarios:
- Missing API keys → Initialization failure
- Invalid prompt names → File not found errors  
- Validation failures → Detailed error dictionaries
- Network issues → OpenAI client exceptions

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-mock

# Run all tests
python -m pytest tests/ -v

# Run specific test category
python -m pytest tests/test_schema_validator.py -v

# Run with coverage
python -m pytest tests/ --cov=ai_manager --cov-report=html
```

### Test Configuration

Set environment variables for testing:

```bash
export OPENAI_API_KEY="your-test-key"
export OPENAI_ORG_ID="your-test-org" 
```

## Examples

### Customer Support Bot

```python
# prompts/support_response.txt
Respond to this customer inquiry: {inquiry}
Customer tier: {tier}
Previous context: {context}

# schemas/support_response.schema.txt  
{
  "response": "Thank you for contacting us...",
  "sentiment": "positive",
  "escalate": false,
  "suggested_actions": ["send_followup", "update_account"],
  "confidence": 0.9
}

# Usage
response = ai_manager.chat('support_response', {
    'inquiry': 'My order is delayed',
    'tier': 'premium', 
    'context': 'Second inquiry this month'
}, validate=True)

if response.get('escalate'):
    escalate_to_human(response)
```

### Data Analysis Pipeline

```python
# Structured data analysis
results = ai_manager.chat('analyze_sales', {
    'period': 'Q1 2025',
    'data_source': 'sales_database.csv'
}, validate=True)

# Process results
for insight in results['analysis']['insights']:
    send_to_dashboard(insight)
    
if results['analysis']['confidence'] > 0.8:
    auto_generate_report(results)
```

### Content Generation

```python
# Generate blog post with metadata
post = ai_manager.chat('create_blog_post', {
    'topic': 'AI in Healthcare',
    'target_audience': 'medical professionals',
    'word_count': 1500
}, validate=True)

# Automatic processing
save_to_cms(post['content'])
schedule_publication(post['publish_date'])
tag_with_categories(post['tags'])
```

## License

BSD 3-Clause License

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`python -m pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

## Support

- **Issues**: GitHub Issues for bug reports and feature requests
- **Documentation**: This README and inline code documentation
- **Examples**: See `examples/` directory for more use cases