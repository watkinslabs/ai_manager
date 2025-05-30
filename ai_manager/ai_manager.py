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