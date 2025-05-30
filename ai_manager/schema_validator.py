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