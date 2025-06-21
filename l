## Florted: 2025-06-20 18:13:21
Processing 8 files from 1 directories -> stdio
## Directory Tree
ai_manager/
├── __init__.py
├── ai_manager.py
├── chat.py
├── openai.py
├── prompts.py
├── schema_validator.py
├── text_to_speech.py
└── transcribe.py

## File Data
--- File: __init__.py
--- Characters: 175
--- Token Count: 25
from .transcribe import  transcribe_audio
from .text_to_speech import generate_speech
from .chat import chat
from .prompts import get_prompts
from .ai_manager import AIManager

--- File: ai_manager.py
--- Characters: 10,678
--- Token Count: 1,698
import logging
import os
from pathlib import Path

from .chat import chat
from .openai import init_openai_client
from .prompts import get_prompts
from .text_to_speech import generate_speech
from .transcribe import transcribe_audio
from .schema_validator import SchemaValidator

class AIManager:
    """
    Wrapper class for AI Manager functionality.
    Initializes OpenAI client and provides access to all functions.
    """

    def __init__(self, config):
        """
        Initialize the AI Manager with configuration.

        Args:
            config: Configuration object with OpenAI settings
        """
        self.config = config
        self.client = init_openai_client(config)
        self.prompts = get_prompts(config)
        self.schema_validator = SchemaValidator(config)
        self.logger = logging.getLogger(__name__)

        if not self.client:
            self.logger.error("Failed to initialize OpenAI client")

    def chat(self, prompt_name, data={}, model=None, validate=False):
        """
        Generate chat completion with optional validation and retry logic.

        Args:
            prompt_name: Name of the prompt to use
            data: Dictionary of data to format the prompt with
            model: OpenAI model to use (defaults to config value)
            validate: Whether to use schema validation with retries (defaults to False)

        Returns:
            Generated text, structured data if validate=True, or error dict on failure
        """
        if not model:
            model = self.config.openai.chat_model

        # Check if validation requested and schema available
        if validate and not self.schema_validator.has_schema_for_prompt(prompt_name):
            self.logger.error(f"Validation requested but no schema found for prompt '{prompt_name}'")
            return {
                'error': f"No schema available for prompt '{prompt_name}'",
                'prompt_name': prompt_name
            }

        max_retries = getattr(self.config, 'max_validation_retries', 3)

        if validate:
            return self._chat_with_validation(prompt_name, data, model, max_retries)
        else:
            # Normal chat without validation
            return chat(
                prompt_name=prompt_name,
                data=data,
                model=model,
                client=self.client,
                prompts=self.prompts
            )

    def _chat_with_validation(self, prompt_name, data, model, max_retries):
        """
        Internal method to handle validated chat with retries.

        Args:
            prompt_name: Name of the prompt
            data: Data for prompt formatting
            model: OpenAI model
            max_retries: Maximum retry attempts

        Returns:
            Structured data or error dict
        """
        schema_content = self.schema_validator.get_schema_content(prompt_name)
        if not schema_content:
            return {
                'error': f"Schema content not found for prompt '{prompt_name}'",
                'prompt_name': prompt_name
            }

        # Get base prompt
        base_prompt = self.prompts.get(prompt_name)
        if not base_prompt:
            return {
                'error': f"Prompt '{prompt_name}' not found",
                'prompt_name': prompt_name
            }

        # Handle dict vs string prompts
        if isinstance(base_prompt, dict):
            if 'user' in base_prompt:
                base_user_prompt = base_prompt['user']
            else:
                self.logger.warning(f"Dict prompt '{prompt_name}' missing 'user' key")
                base_user_prompt = str(base_prompt)
        else:
            base_user_prompt = base_prompt

        # Get template from config or use default
        template = getattr(self.config, 'schema_prompt_template', None)
        combined_prompt = self.schema_validator.create_schema_prompt(
            base_user_prompt,
            schema_content,
            template
        )

        # Create modified prompt for validation
        if isinstance(base_prompt, dict):
            modified_prompt = base_prompt.copy()
            modified_prompt['user'] = combined_prompt
        else:
            modified_prompt = combined_prompt

        # Retry loop
        for attempt in range(max_retries + 1):
            try:
                # Use temporary prompts dict
                temp_prompts = self.prompts.copy()
                temp_prompts[prompt_name] = modified_prompt

                response = chat(
                    prompt_name=prompt_name,
                    data=data,
                    model=model,
                    client=self.client,
                    prompts=temp_prompts
                )

                if not response:
                    self.logger.error(f"Empty response on attempt {attempt + 1}")
                    continue

                # Validate and sanitize response
                validation_result = self.schema_validator.validate_structured_response(response)

                if validation_result['valid']:
                    self.logger.info(f"Validation successful on attempt {attempt + 1}")
                    return validation_result['data']
                else:
                    self.logger.warning(f"Validation failed on attempt {attempt + 1}: {validation_result['errors']}")

                    # If this is the last attempt, return the failure details
                    if attempt == max_retries:
                        return {
                            'error': 'Validation failed after all retries',
                            'attempts': attempt + 1,
                            'last_response': response,
                            'validation_result': validation_result,
                            'prompt_name': prompt_name
                        }

            except Exception as e:
                self.logger.error(f"Exception on attempt {attempt + 1}: {e}")
                if attempt == max_retries:
                    return {
                        'error': f'Exception after all retries: {str(e)}',
                        'attempts': attempt + 1,
                        'prompt_name': prompt_name
                    }

        return {
            'error': 'Unexpected failure in validation loop',
            'prompt_name': prompt_name
        }

    def get_schema_prompts(self):
        """
        Get list of prompts that have corresponding .schema.txt files.

        Returns:
            List of prompt names that have schema examples available
        """
        available_schemas = set(self.schema_validator.list_schemas())
        available_prompts = set(self.prompts.keys())
        return list(available_schemas.intersection(available_prompts))

    def validate_response_for_prompt(self, response, prompt_name):
        """
        Validate a structured response (JSON/YAML).

        Args:
            response: Response text to validate
            prompt_name: Name of prompt (for logging purposes)

        Returns:
            Dict with validation results
        """
        return self.schema_validator.validate_structured_response(response)

    def has_schema_for_prompt(self, prompt_name):
        """
        Check if a schema exists for the given prompt.

        Args:
            prompt_name: Name of the prompt

        Returns:
            True if schema exists for this prompt
        """
        return self.schema_validator.has_schema_for_prompt(prompt_name)

    def validate_data(self, data, schema_name):
        """
        Validate arbitrary data against a named schema.

        Args:
            data: Data to validate
            schema_name: Name of schema to validate against

        Returns:
            Dict with validation results
        """
        return self.schema_validator.validate_data(data, schema_name)

    def add_schema(self, name, schema):
        """
        Add a schema programmatically.

        Args:
            name: Name for the schema
            schema: JSON schema dictionary
        """
        self.schema_validator.add_schema(name, schema)

    def get_available_schemas(self):
        """
        Get list of available schema names (which match prompt names).

        Returns:
            List of schema names
        """
        return self.schema_validator.list_schemas()

    def get_schema_prompts(self):
        """
        Get list of prompts that have .schema.txt suffix and corresponding schemas.

        Returns:
            List of base prompt names that have both .schema.txt prompts and .schema.json schemas
        """
        schema_prompts = []
        for prompt_name in self.prompts.keys():
            if prompt_name.endswith('.schema'):
                base_name = prompt_name.replace('.schema', '')
                if self.schema_validator.has_schema_for_prompt(base_name):
                    schema_prompts.append(base_name)
        return schema_prompts

    def generate_speech(self, text, voice=None, model=None, output_path=None):
        """
        Generate speech from text.

        Args:
            text: Text to convert to speech
            voice: Voice to use (defaults to config value)
            model: TTS model to use (defaults to config value)
            output_path: Path where to save WAV file (optional)

        Returns:
            True on success or None on failure
        """
        if not voice:
            voice = self.config.openai.tts_voice

        if not model:
            model = self.config.openai.tts_model

        if not output_path:
            # Generate a default output path if none provided
            output_dir = Path(self.config.output_dir) / "speech"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"speech_{os.urandom(4).hex()}.wav"

        return generate_speech(
            text=text,
            voice=voice,
            model=model,
            output_path=str(output_path),
            client=self.client
        )

    def transcribe_audio(self, audio_data=None, audio_path=None):
        """
        Transcribe audio using Whisper API.

        Args:
            audio_data: Raw binary data or numpy array
            audio_path: Path to audio file

        Returns:
            Transcribed text or None on failure
        """
        return transcribe_audio(
            audio_data=audio_data,
            audio_path=audio_path,
            client=self.client
        )

    def get_prompts(self):
        """
        Get available prompts.

        Returns:
            Dictionary of prompts
        """
        return self.prompts

--- File: chat.py
--- Characters: 2,962
--- Token Count: 571
import re
import os
import io
import requests
from datetime import datetime
import openai
import logging

logger = logging.getLogger(__name__)

def chat(prompt_name, data={}, model=None, client=None,prompts=None):
    messages = []
    try:
        if not data:
            data = {}
        logging.info(f"Generating content with data: {data}")

        if not client:
            logger.error("No OpenAI client available")
            return None

        # Validate prompt existence
        if prompt_name not in prompts:
            logging.error(f"Prompt '{prompt_name}' not found in available prompts.")
            return None

        prompt = prompts[prompt_name]
        if prompt is None:
            logging.error(f"Prompt '{prompt_name}' exists but is None.")
            return None

        # Extract placeholders from the prompt
        def extract_placeholders(prompt_text):
            if not prompt_text:  # Handle None or empty string
                return []
            return re.findall(r'{(.*?)}', prompt_text)

        required_keys = set()
        if isinstance(prompt, dict):
            if 'user' in prompt and prompt['user']:
                required_keys.update(extract_placeholders(prompt['user']))
        elif prompt:  # Only process if prompt is not None or empty
            required_keys.update(extract_placeholders(prompt))

        # Check if all required keys are present in the data
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            logging.error(f"Missing required data keys for formatting: {missing_keys}")
            return None

        # Build messages based on prompt structure
        if isinstance(prompt, dict):
            if 'system' in prompt and prompt['system']:
                messages.append({
                    "role": "system",
                    "content": prompt['system']
                })
            if 'user' in prompt and prompt['user']:
                messages.append({
                    "role": "user",
                    "content": prompt['user'].format(**data)
                })
        elif prompt:  # Only process if prompt is not None or empty
            messages.append({
                "role": "user",
                "content": prompt.format(**data)
            })

        # Check if messages is empty
        if not messages:
            logging.error("No messages created from prompt")
            return None

        # Send request to the OpenAI client
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )

        result = response.choices[0].message.content.strip()
        logging.info("Content generation successful.")
        return result

    except KeyError as key_err:
        logging.error(f"KeyError: Missing data for formatting - {key_err}")
    except Exception as ex:
        logging.error(f"Error during content generation: {ex}")

    return None

--- File: openai.py
--- Characters: 650
--- Token Count: 106
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


def init_openai_client(config):
    """
    Initialize the OpenAI client using configuration.

    Args:
        config: Configuration object with openai settings

    Returns:
        OpenAI: Initialized OpenAI client or None on failure
    """
    try:
        # Access configuration using dot notation
        client = OpenAI(
            api_key=config.openai.api_key,
            organization=config.openai.organization_id
        )
        return client
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")
        return None

--- File: prompts.py
--- Characters: 3,621
--- Token Count: 654
import os
import logging

logger = logging.getLogger(__name__)


def get_prompts(config):
    """
    Load prompt templates from the configured prompt folder.

    Args:
        config: Configuration object containing prompt_folder path

    Returns:
        dict: Dictionary of prompt templates
    """
    directory_path = config.prompt_folder
    prompts = {}
    system_count = 0
    user_count = 0
    standard_count = 0

    try:
        # Check if directory exists
        if not os.path.exists(directory_path):
            logging.error(f"Prompt directory not found: {directory_path}")
            return prompts

        if not os.path.isdir(directory_path):
            logging.error(f"Prompt path is not a directory: {directory_path}")
            return prompts

        file_list = os.listdir(directory_path)
        logging.info(f"Found {len(file_list)} files in prompt directory")

        for filename in file_list:
            try:
                if not filename.endswith('.txt'):
                    logging.debug(f"Skipping non-txt file: {filename}")
                    continue

                basename = filename.split('.')[0]
                file_path = os.path.join(directory_path, filename)

                # Check if file is readable
                if not os.access(file_path, os.R_OK):
                    logging.warning(f"Cannot read prompt file (permission denied): {file_path}")
                    continue

                with open(file_path, 'r') as file:
                    try:
                        content = file.read()
                        if not content.strip():
                            logging.warning(f"Empty prompt file: {file_path}")
                            continue

                        if '.system.txt' in filename:
                            if basename not in prompts:
                                prompts[basename] = {}
                            prompts[basename]['system'] = content
                            system_count += 1
                            logging.debug(f"Loaded system prompt: {basename}")
                        elif '.user.txt' in filename:
                            if basename not in prompts:
                                prompts[basename] = {}
                            prompts[basename]['user'] = content
                            user_count += 1
                            logging.debug(f"Loaded user prompt: {basename}")
                        else:
                            prompts[basename] = content
                            standard_count += 1
                            logging.debug(f"Loaded standard prompt: {basename}")
                    except UnicodeDecodeError as e:
                        logging.error(f"Failed to decode file {file_path}: {str(e)}")
            except Exception as e:
                logging.error(f"Error processing prompt file {filename}: {str(e)}")

        logging.info(f"Loaded {len(prompts)} prompt templates (system: {system_count}, user: {user_count}, standard: {standard_count})")

        # Validate that prompts with 'system' also have 'user' parts
        for name, prompt in prompts.items():
            if isinstance(prompt, dict):
                if 'system' in prompt and 'user' not in prompt:
                    logging.warning(f"Prompt {name} has system part but missing user part")
                if 'user' in prompt and 'system' not in prompt:
                    logging.warning(f"Prompt {name} has user part but missing system part")

    except Exception as e:
        logging.error(f"Failed to load prompts: {str(e)}")

    return prompts

--- File: schema_validator.py
--- Characters: 12,377
--- Token Count: 2,214
"""
Schema validation module for ai_manager.
Provides JSON schema validation for AI responses and data structures.
"""

import json
import logging
from typing import Dict, Any, Optional, Union
from jsonschema import validate, ValidationError, Draft7Validator

logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    JSON Schema validator for AI Manager responses and data.
    """

    def __init__(self, config=None):
        """
        Initialize the schema validator.

        Args:
            config: Configuration object with schema settings
        """
        self.config = config
        self.schemas = {}
        self.logger = logging.getLogger(__name__)

        if config and hasattr(config, 'schema_folder'):
            self.load_schemas_from_folder(config.schema_folder)

    def load_schemas_from_folder(self, schema_folder: str) -> None:
        """
        Load schemas from .schema.txt files.
        Schema files contain example JSON/YAML structure for prompts.

        Args:
            schema_folder: Path to folder containing .schema.txt files
        """
        import os

        if not os.path.exists(schema_folder):
            self.logger.warning(f"Schema folder not found: {schema_folder}")
            return

        try:
            for filename in os.listdir(schema_folder):
                if filename.endswith('.schema.txt'):
                    # Remove .schema.txt to get base prompt name
                    schema_name = filename.replace('.schema.txt', '')
                    schema_path = os.path.join(schema_folder, filename)

                    with open(schema_path, 'r') as f:
                        schema_content = f.read().strip()
                        if schema_content:
                            self.schemas[schema_name] = schema_content
                            self.logger.debug(f"Loaded schema for prompt: {schema_name}")

            self.logger.info(f"Loaded {len(self.schemas)} schemas from {schema_folder}")

        except Exception as e:
            self.logger.error(f"Error loading schemas from folder: {e}")

    def create_schema_prompt(self, base_prompt: str, schema_content: str, template: str = None) -> str:
        """
        Create a prompt that includes schema example for structured output.

        Args:
            base_prompt: The original user prompt
            schema_content: Schema example content (JSON/YAML)
            template: Optional template for combining prompt and schema

        Returns:
            Combined prompt with schema instructions
        """
        if template:
            # Use custom template if provided
            return template.format(
                base_prompt=base_prompt,
                schema_example=schema_content
            )

        # Default template
        default_template = """{base_prompt}

Please respond with structured data in the following format:

{schema_example}

Return only the structured data without any additional text or explanations."""

        return default_template.format(
            base_prompt=base_prompt,
            schema_example=schema_content
        )

    def add_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """
        Add a schema programmatically.

        Args:
            name: Name for the schema
            schema: JSON schema dictionary
        """
        try:
            # Validate that the schema itself is valid
            Draft7Validator.check_schema(schema)
            self.schemas[name] = schema
            self.logger.debug(f"Added schema: {name}")
        except Exception as e:
            self.logger.error(f"Invalid schema for '{name}': {e}")
            raise

    def validate_data(self, data: Any, schema_name: str) -> Dict[str, Any]:
        """
        Validate data against a named schema.

        Args:
            data: Data to validate
            schema_name: Name of schema to validate against

        Returns:
            Dict with 'valid' bool and 'errors' list
        """
        if schema_name not in self.schemas:
            error_msg = f"Schema '{schema_name}' not found"
            self.logger.error(error_msg)
            return {
                'valid': False,
                'errors': [error_msg]
            }

        return self.validate_data_with_schema(data, self.schemas[schema_name])

    def validate_data_with_schema(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against a provided schema.

        Args:
            data: Data to validate
            schema: JSON schema dictionary

        Returns:
            Dict with 'valid' bool and 'errors' list
        """
        try:
            validate(instance=data, schema=schema)
            return {
                'valid': True,
                'errors': []
            }
        except ValidationError as e:
            error_details = {
                'message': e.message,
                'path': list(e.path) if e.path else [],
                'invalid_value': e.instance
            }
            self.logger.debug(f"Validation error: {error_details}")
            return {
                'valid': False,
                'errors': [error_details]
            }
        except Exception as e:
            error_msg = f"Schema validation failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'valid': False,
                'errors': [error_msg]
            }

    def validate_json_string(self, json_string: str, schema_name: str) -> Dict[str, Any]:
        """
        Parse JSON string and validate against schema.

        Args:
            json_string: JSON string to parse and validate
            schema_name: Name of schema to validate against

        Returns:
            Dict with 'valid' bool, 'errors' list, and 'data' if valid
        """
        try:
            data = json.loads(json_string)
            result = self.validate_data(data, schema_name)
            if result['valid']:
                result['data'] = data
            return result
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {str(e)}"
            self.logger.error(error_msg)
            return {
                'valid': False,
                'errors': [error_msg]
            }

    def get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a schema by name.

        Args:
            schema_name: Name of the schema

        Returns:
            Schema dictionary or None if not found
        """
        return self.schemas.get(schema_name)

    def has_schema_for_prompt(self, prompt_name: str) -> bool:
        """
        Check if a schema exists for the given prompt name.
        This checks for schemas that correspond to .schema.txt prompts.

        Args:
            prompt_name: Base name of the prompt (without .schema.txt)

        Returns:
            True if schema exists for this prompt
        """
        return prompt_name in self.schemas

    def get_schema_content(self, prompt_name: str) -> Optional[str]:
        """
        Get the schema content for a prompt.

        Args:
            prompt_name: Name of the prompt

        Returns:
            Schema content string or None if not found
        """
        return self.schemas.get(prompt_name)

    def sanitize_response(self, response: str) -> str:
        """
        Sanitize LLM response by removing common wrapper text and extracting JSON/YAML.

        Args:
            response: Raw LLM response

        Returns:
            Cleaned response string
        """
        if not response:
            return response

        # Remove common wrapper phrases
        lines = response.strip().split('\n')
        cleaned_lines = []

        skip_patterns = [
            'here is the',
            'here\'s the',
            'the json is',
            'the yaml is',
            'response:',
            'result:',
            'output:',
            '```json',
            '```yaml',
            '```'
        ]

        for line in lines:
            line_lower = line.lower().strip()

            # Skip lines that match wrapper patterns
            if any(pattern in line_lower for pattern in skip_patterns):
                continue

            # Skip empty lines at start
            if not cleaned_lines and not line.strip():
                continue

            cleaned_lines.append(line)

        # Remove trailing empty lines and closing code blocks
        while cleaned_lines and (not cleaned_lines[-1].strip() or cleaned_lines[-1].strip() == '```'):
            cleaned_lines.pop()

        return '\n'.join(cleaned_lines).strip()

    def validate_structured_response(self, response: str) -> Dict[str, Any]:
        """
        Validate a structured response (JSON or YAML) and parse it.
        Automatically sanitizes the response first.

        Args:
            response: Response string to validate and parse

        Returns:
            Dict with validation results and parsed data
        """
        import yaml

        # First sanitize the response
        sanitized = self.sanitize_response(response)

        if not sanitized:
            return {
                'valid': False,
                'data': None,
                'format': 'unknown',
                'errors': ['Empty response after sanitization']
            }

        # Try JSON first
        try:
            data = json.loads(sanitized)
            return {
                'valid': True,
                'data': data,
                'format': 'json',
                'errors': [],
                'sanitized_response': sanitized
            }
        except json.JSONDecodeError as json_err:
            pass

        # Try YAML
        try:
            data = yaml.safe_load(sanitized)
            if data is not None:  # YAML can return None for empty strings
                return {
                    'valid': True,
                    'data': data,
                    'format': 'yaml',
                    'errors': [],
                    'sanitized_response': sanitized
                }
        except yaml.YAMLError as yaml_err:
            return {
                'valid': False,
                'data': None,
                'format': 'unknown',
                'errors': [f"JSON error: {str(json_err)}", f"YAML error: {str(yaml_err)}"],
                'sanitized_response': sanitized
            }

        return {
            'valid': False,
            'data': None,
            'format': 'unknown',
            'errors': ['Response is neither valid JSON nor YAML after sanitization'],
            'sanitized_response': sanitized
        }

    def list_schemas(self) -> list:
        """
        Get list of available schema names.

        Returns:
            List of schema names
        """
        return list(self.schemas.keys())

    def validate_ai_response(self, response: str, expected_format: str = 'json') -> Dict[str, Any]:
        """
        Validate AI response format and extract structured data.

        Args:
            response: AI response string
            expected_format: Expected format ('json', 'structured_text', etc.)

        Returns:
            Dict with validation results and extracted data
        """
        if expected_format == 'json':
            try:
                data = json.loads(response)
                return {
                    'valid': True,
                    'data': data,
                    'format': 'json',
                    'errors': []
                }
            except json.JSONDecodeError as e:
                return {
                    'valid': False,
                    'data': None,
                    'format': 'unknown',
                    'errors': [f"Invalid JSON: {str(e)}"]
                }
        else:
            # For other formats, just return the response as valid text
            return {
                'valid': True,
                'data': response,
                'format': 'text',
                'errors': []
            }


def create_schema_validator(config=None) -> SchemaValidator:
    """
    Factory function to create a schema validator.

    Args:
        config: Configuration object

    Returns:
        SchemaValidator instance
    """
    return SchemaValidator(config)

--- File: text_to_speech.py
--- Characters: 1,534
--- Token Count: 309
"""
Text-to-Speech generator for audio_manager.
Provides TTS functionality using OpenAI's API.
"""

import logging
import os
from pathlib import Path
import uuid
import openai

from .openai import init_openai_client

logger = logging.getLogger(__name__)


def generate_speech(text, voice, model, output_path, client=None):
    """
    Generate speech using OpenAI's TTS API and save it as WAV file.

    Args:
        text: Text to convert to speech
        voice: Voice to use
        model: TTS model to use
        output_path: Path where to save WAV file
        config: Configuration object with openai settings

    Returns:
        str: True on success or None on failure
    """
    try:

        # Ensure output directory exists
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if not client:
            logger.error("No OpenAI client available")
            return None

        # Generate speech using OpenAI API
        logger.info(f"Generating TTS for: '{text[:50]}...' using voice: {voice}, model: {model}")

        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="wav"
        )

        # Save WAV file
        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info(f"Saved WAV file: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        return None

--- File: transcribe.py
--- Characters: 2,901
--- Token Count: 529
"""
Transcription module for audio_manager.
Provides audio transcription functionality using OpenAI's Whisper API.
"""

import os
import logging
import wave
import tempfile
from pathlib import Path
import soundfile as sf
import openai

logger = logging.getLogger(__name__)

def transcribe_audio(audio_data=None, audio_path=None, client=None):
    """
    Transcribe audio using OpenAI Whisper API

    Args:
        audio_data: Can be either raw binary data or numpy array
        audio_path: Optional existing file path that contains audio
        config: Configuration object with openai settings
        client: Optional pre-initialized OpenAI client

    Returns:
        The transcribed text or None on failure
    """
    logger.debug(f"Transcribing audio, data type: {type(audio_data) if audio_data else 'None'}, path: {audio_path}")


    if audio_data is None and (not audio_path or not os.path.exists(audio_path)):
        logger.error("No valid audio data or path provided")
        return None

    if not client:
        logger.error("No OpenAI client available")
        return None

    try:
        # If audio_path is provided and file exists, use it directly
        if audio_path and os.path.exists(audio_path):
            logger.debug(f"Using existing audio file: {audio_path}")
            with open(audio_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model=config.openai.whisper_model,
                    file=audio_file
                )
        # Otherwise, create a temporary file
        else:
            temp_dir = getattr(config, "temp_dir", "/tmp")
            sample_rate = getattr(config, "sample_rate", 44100)

            logger.debug(f"Creating temporary file for transcription in {temp_dir}")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name

                # If audio_data is binary, write directly
                if isinstance(audio_data, bytes):
                    f.write(audio_data)
                # Otherwise assume it's a numpy array
                else:
                    sf.write(f.name, audio_data, sample_rate, format='WAV')

            try:
                logger.debug(f"Opening temp file for transcription: {temp_path}")
                with open(temp_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model=config.openai.whisper_model,
                        file=audio_file
                    )
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        logger.info(f"Transcription result: {transcript.text}")
        return transcript.text

    except Exception as e:
        logger.error(f"Error in transcription: {e}")
        return None


## Concatenation Summary
Files processed: 8
Files skipped: 0
Total characters: 34,898
Total tokens: 6,106

Completed at: 2025-06-20 18:13:22

Flort completed successfully!
