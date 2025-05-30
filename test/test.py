"""
Unit tests for AI Manager using JSON test data
"""

import unittest
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_manager import AIManager
from ai_manager import AIManager
from ai_manager.schema_validator import SchemaValidator
from test_config import get_test_config


class TestDataLoader:
    """Helper class to load and manage test data from JSON"""
    
    def __init__(self, data_file="./test_data/test_data.json"):
        self.data_file = Path(data_file)
        self._data = None
    
    @property
    def data(self):
        if self._data is None:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    self._data = json.load(f)
            else:
                raise FileNotFoundError(f"Test data file not found: {self.data_file}")
        return self._data
    
    def get_simple_prompts(self):
        return self.data['simple_prompts']
    
    def get_structured_prompts(self):
        return self.data['structured_prompts']
    
    def get_system_user_prompts(self):
        return self.data['system_user_prompts']
    
    def get_test_scenarios(self):
        return self.data['test_scenarios']
    
    def get_prompt_info(self, prompt_name):
        """Get prompt info from any category"""
        for category in ['simple_prompts', 'structured_prompts', 'system_user_prompts']:
            if prompt_name in self.data[category]:
                return self.data[category][prompt_name]
        return None


# Global test data loader
test_data_loader = TestDataLoader()


class TestSchemaValidator(unittest.TestCase):
    """Test cases for SchemaValidator"""
    
    def setUp(self):
        self.config = get_test_config()
        self.validator = SchemaValidator(self.config)
        self.test_data = test_data_loader
        
    def test_sanitize_response(self):
        """Test response sanitization"""
        # Test removing wrapper text
        response = """Here is the JSON:
```json
{"name": "test", "value": 123}
```"""
        expected = '{"name": "test", "value": 123}'
        result = self.validator.sanitize_response(response)
        self.assertEqual(result, expected)
        
        # Test removing multiple wrapper patterns
        response = """The response is:
Here's the result:
{"data": "clean"}
"""
        expected = '{"data": "clean"}'
        result = self.validator.sanitize_response(response)
        self.assertEqual(result, expected)
    
    def test_validate_structured_response_json(self):
        """Test JSON validation"""
        response = '{"name": "Alice", "age": 30}'
        result = self.validator.validate_structured_response(response)
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['format'], 'json')
        self.assertEqual(result['data']['name'], 'Alice')
        self.assertEqual(result['data']['age'], 30)
    
    def test_validate_structured_response_yaml(self):
        """Test YAML validation"""
        response = """name: Bob
age: 25
active: true"""
        result = self.validator.validate_structured_response(response)
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['format'], 'yaml')
        self.assertEqual(result['data']['name'], 'Bob')
        self.assertEqual(result['data']['age'], 25)
        self.assertTrue(result['data']['active'])
    
    def test_validate_structured_response_invalid(self):
        """Test invalid response validation"""
        response = "This is not JSON or YAML {invalid"
        result = self.validator.validate_structured_response(response)
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['format'], 'unknown')
        self.assertIsNone(result['data'])
        self.assertIn('errors', result)
    
    def test_has_schema_for_prompts_from_data(self):
        """Test schema availability checking using test data"""
        # Get prompts that should have schemas
        structured_prompts = self.test_data.get_structured_prompts()
        system_user_prompts = self.test_data.get_system_user_prompts()
        
        for prompt_name in structured_prompts:
            self.assertTrue(self.validator.has_schema_for_prompt(prompt_name),
                          f"Should have schema for {prompt_name}")
        
        # Check system/user prompts with schemas
        for prompt_name, info in system_user_prompts.items():
            if 'schema_yaml' in info:
                self.assertTrue(self.validator.has_schema_for_prompt(prompt_name),
                              f"Should have schema for {prompt_name}")
        
        # Should not have schema for simple prompts
        simple_prompts = self.test_data.get_simple_prompts()
        for prompt_name in simple_prompts:
            self.assertFalse(self.validator.has_schema_for_prompt(prompt_name),
                           f"Should not have schema for {prompt_name}")


class TestAIManagerInit(unittest.TestCase):
    """Test AIManager initialization"""
    
    def setUp(self):
        self.config = get_test_config()
        self.test_data = test_data_loader
        
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_ai_manager_init(self, mock_init_client):
        """Test AIManager initialization"""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        ai_manager = AIManager(self.config)
        
        self.assertEqual(ai_manager.config, self.config)
        self.assertEqual(ai_manager.client, mock_client)
        self.assertIsInstance(ai_manager.schema_validator, SchemaValidator)
        self.assertIsInstance(ai_manager.prompts, dict)
        mock_init_client.assert_called_once_with(self.config)
    
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_prompts_loaded_from_data(self, mock_init_client):
        """Test that prompts are loaded correctly based on test data"""
        mock_init_client.return_value = Mock()
        
        ai_manager = AIManager(self.config)
        
        # Check simple prompts
        simple_prompts = self.test_data.get_simple_prompts()
        for prompt_name in simple_prompts:
            self.assertIn(prompt_name, ai_manager.prompts,
                         f"Simple prompt {prompt_name} should be loaded")
        
        # Check structured prompts
        structured_prompts = self.test_data.get_structured_prompts()
        for prompt_name in structured_prompts:
            self.assertIn(prompt_name, ai_manager.prompts,
                         f"Structured prompt {prompt_name} should be loaded")
        
        # Check system/user prompts
        system_user_prompts = self.test_data.get_system_user_prompts()
        for prompt_name in system_user_prompts:
            self.assertIn(prompt_name, ai_manager.prompts,
                         f"System/user prompt {prompt_name} should be loaded")
            # Check structure
            prompt = ai_manager.prompts[prompt_name]
            self.assertIsInstance(prompt, dict)
            self.assertIn('system', prompt)
            self.assertIn('user', prompt)


class TestAIManagerChat(unittest.TestCase):
    """Test AIManager chat functionality with test data"""
    
    def setUp(self):
        self.config = get_test_config()
        self.test_data = test_data_loader
        
    @patch('ai_manager.ai_manager.chat')
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_chat_simple_prompts(self, mock_init_client, mock_chat_func):
        """Test chat with simple prompts from test data"""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        ai_manager = AIManager(self.config)
        
        simple_prompts = self.test_data.get_simple_prompts()
        
        for prompt_name, info in simple_prompts.items():
            mock_chat_func.return_value = f"Response for {prompt_name}"
            
            result = ai_manager.chat(prompt_name, info['test_data'])
            
            self.assertEqual(result, f"Response for {prompt_name}")
            # Verify the chat function was called with correct parameters
            args, kwargs = mock_chat_func.call_args
            self.assertEqual(kwargs['prompt_name'], prompt_name)
            self.assertEqual(kwargs['data'], info['test_data'])
    
    @patch('ai_manager.ai_manager.chat')
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_chat_structured_validation_success(self, mock_init_client, mock_chat_func):
        """Test validated chat with structured prompts"""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        ai_manager = AIManager(self.config)
        
        structured_prompts = self.test_data.get_structured_prompts()
        
        for prompt_name, info in structured_prompts.items():
            # Use the mock response from test data
            mock_chat_func.return_value = info['mock_response']
            
            result = ai_manager.chat(prompt_name, info['test_data'], validate=True)
            
            # Should return parsed data
            self.assertIsInstance(result, dict)
            
            # Check expected fields are present
            for field in info['expected_fields']:
                self.assertIn(field, result, f"Missing field {field} in {prompt_name} response")
    
    @patch('ai_manager.ai_manager.chat')
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_chat_yaml_validation(self, mock_init_client, mock_chat_func):
        """Test YAML validation with system/user prompts"""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        ai_manager = AIManager(self.config)
        
        system_user_prompts = self.test_data.get_system_user_prompts()
        
        for prompt_name, info in system_user_prompts.items():
            if 'mock_response' in info:  # Only test prompts with mock responses
                mock_chat_func.return_value = info['mock_response']
                
                result = ai_manager.chat(prompt_name, info['test_data'], validate=True)
                
                # Should return parsed YAML data
                self.assertIsInstance(result, dict)
                
                # Check expected fields
                if 'expected_fields' in info:
                    for field in info['expected_fields']:
                        self.assertIn(field, result, f"Missing field {field} in {prompt_name} response")
    
    def test_validation_scenarios(self):
        """Test specific validation scenarios from test data"""
        scenarios = self.test_data.get_test_scenarios()
        
        with patch('ai_manager.ai_manager.init_openai_client') as mock_init_client:
            mock_init_client.return_value = Mock()
            ai_manager = AIManager(self.config)
            
            # Test missing schema scenario
            missing_schema = scenarios['missing_schema']
            result = ai_manager.chat(
                missing_schema['prompt'], 
                missing_schema['data'], 
                validate=missing_schema['validate']
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn('error', result)
            self.assertIn('No schema available', result['error'])
    
    @patch('ai_manager.ai_manager.chat')
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_validation_failure_retries(self, mock_init_client, mock_chat_func):
        """Test validation failure with retries"""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        scenarios = self.test_data.get_test_scenarios()
        failure_scenario = scenarios['validation_failure']
        
        # Always return invalid response
        mock_chat_func.return_value = failure_scenario['mock_invalid_response']
        
        ai_manager = AIManager(self.config)
        result = ai_manager.chat(
            failure_scenario['prompt'], 
            failure_scenario['data'], 
            validate=True
        )
        
        # Should return error dict after max retries
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)
        self.assertIn('attempts', result)
    
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_get_schema_prompts_from_data(self, mock_init_client):
        """Test getting schema prompts based on test data"""
        mock_init_client.return_value = Mock()
        ai_manager = AIManager(self.config)
        
        schema_prompts = ai_manager.get_schema_prompts()
        
        # Should include all structured prompts
        structured_prompts = self.test_data.get_structured_prompts()
        for prompt_name in structured_prompts:
            self.assertIn(prompt_name, schema_prompts)
        
        # Should include system/user prompts with schemas
        system_user_prompts = self.test_data.get_system_user_prompts()
        for prompt_name, info in system_user_prompts.items():
            if 'schema_yaml' in info:
                self.assertIn(prompt_name, schema_prompts)
        
        # Should not include simple prompts
        simple_prompts = self.test_data.get_simple_prompts()
        for prompt_name in simple_prompts:
            self.assertNotIn(prompt_name, schema_prompts)


class TestAIManagerTTS(unittest.TestCase):
    """Test AIManager text-to-speech functionality"""
    
    @patch('ai_manager.ai_manager.generate_speech')
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_generate_speech_with_defaults(self, mock_init_client, mock_generate_speech):
        """Test TTS generation with default parameters"""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        mock_generate_speech.return_value = "/test/output.wav"
        
        config = get_test_config()
        ai_manager = AIManager(config)
        result = ai_manager.generate_speech("Hello world")
        
        self.assertEqual(result, "/test/output.wav")
        mock_generate_speech.assert_called_once()
        args, kwargs = mock_generate_speech.call_args
        self.assertEqual(kwargs['text'], "Hello world")
        self.assertEqual(kwargs['client'], mock_client)


class TestAIManagerTranscription(unittest.TestCase):
    """Test AIManager transcription functionality"""
    
    @patch('ai_manager.ai_manager.transcribe_audio')
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_transcribe_audio_from_path(self, mock_init_client, mock_transcribe):
        """Test audio transcription from file path"""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        mock_transcribe.return_value = "Hello world transcription"
        
        config = get_test_config()
        ai_manager = AIManager(config)
        result = ai_manager.transcribe_audio(audio_path="/test/audio.wav")
        
        self.assertEqual(result, "Hello world transcription")
        mock_transcribe.assert_called_once()


class TestIntegrationWithTestData(unittest.TestCase):
    """Integration tests using test data"""
    
    def setUp(self):
        self.config = get_test_config()
        self.test_data = test_data_loader
        
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_full_workflow_all_structured_prompts(self, mock_init_client):
        """Test complete workflow with all structured prompts from test data"""
        mock_client = Mock()
        mock_init_client.return_value = mock_client
        
        structured_prompts = self.test_data.get_structured_prompts()
        
        for prompt_name, info in structured_prompts.items():
            with patch('ai_manager.chat.chat') as mock_chat:
                mock_chat.return_value = info['mock_response']
                
                ai_manager = AIManager(self.config)
                result = ai_manager.chat(
                    prompt_name,
                    info['test_data'],
                    validate=True
                )
                
                self.assertIsInstance(result, dict, f"Failed for prompt: {prompt_name}")
                
                # Verify expected fields
                for field in info['expected_fields']:
                    self.assertIn(field, result, 
                                f"Missing field {field} in {prompt_name} response")
    
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_prompt_content_matches_data(self, mock_init_client):
        """Test that loaded prompts match test data content"""
        mock_init_client.return_value = Mock()
        
        ai_manager = AIManager(self.config)
        
        # Test simple prompts
        simple_prompts = self.test_data.get_simple_prompts()
        for prompt_name, info in simple_prompts.items():
            self.assertIn(prompt_name, ai_manager.prompts)
            self.assertEqual(ai_manager.prompts[prompt_name], info['content'])
        
        # Test structured prompts
        structured_prompts = self.test_data.get_structured_prompts()
        for prompt_name, info in structured_prompts.items():
            self.assertIn(prompt_name, ai_manager.prompts)
            self.assertEqual(ai_manager.prompts[prompt_name], info['content'])
        
        # Test system/user prompts
        system_user_prompts = self.test_data.get_system_user_prompts()
        for prompt_name, info in system_user_prompts.items():
            self.assertIn(prompt_name, ai_manager.prompts)
            prompt = ai_manager.prompts[prompt_name]
            self.assertEqual(prompt['system'], info['system'])
            self.assertEqual(prompt['user'], info['user'])
    
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_schema_content_matches_data(self, mock_init_client):
        """Test that loaded schemas match test data"""
        mock_init_client.return_value = Mock()
        
        ai_manager = AIManager(self.config)
        
        # Test structured prompt schemas
        structured_prompts = self.test_data.get_structured_prompts()
        for prompt_name, info in structured_prompts.items():
            schema_content = ai_manager.schema_validator.get_schema_content(prompt_name)
            self.assertIsNotNone(schema_content)
            
            # Parse and compare schema content
            loaded_schema = json.loads(schema_content)
            expected_schema = info['schema']
            self.assertEqual(loaded_schema, expected_schema)
        
        # Test system/user prompt schemas (YAML)
        system_user_prompts = self.test_data.get_system_user_prompts()
        for prompt_name, info in system_user_prompts.items():
            if 'schema_yaml' in info:
                schema_content = ai_manager.schema_validator.get_schema_content(prompt_name)
                self.assertIsNotNone(schema_content)
                self.assertEqual(schema_content, info['schema_yaml'])


class TestErrorHandlingWithData(unittest.TestCase):
    """Test error handling scenarios using test data"""
    
    def setUp(self):
        self.config = get_test_config()
        self.test_data = test_data_loader
    
    @patch('ai_manager.ai_manager.init_openai_client')
    def test_error_scenarios_from_data(self, mock_init_client):
        """Test error scenarios defined in test data"""
        mock_init_client.return_value = Mock()
        
        scenarios = self.test_data.get_test_scenarios()
        ai_manager = AIManager(self.config)
        
        # Test missing schema scenario
        missing_schema = scenarios['missing_schema']
        with patch('ai_manager.chat.chat') as mock_chat:
            mock_chat.return_value = "Some response"
            result = ai_manager.chat(
                missing_schema['prompt'],
                missing_schema['data'],
                validate=missing_schema['validate']
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn('error', result)
        
        # Test missing data keys scenario
        missing_keys = scenarios['missing_data_keys']
        with patch('ai_manager.chat.chat') as mock_chat:
            mock_chat.return_value = None  # Simulate missing keys error
            result = ai_manager.chat(missing_keys['prompt'], missing_keys['data'])
            
            self.assertIsNone(result)


def setup_test_environment():
    """Setup test environment by generating files from JSON data"""
    import subprocess
    import sys
    
    test_dir = Path(__file__).parent / "test_data"
    
    # Check if test data exists
    if not (test_dir / "test_data.json").exists():
        print("Test data not found. Generating test files...")
        
        # Run the generation script
        script_path = Path(__file__).parent.parent / "generate_test_files.sh"
        if script_path.exists():
            result = subprocess.run([
                "bash", str(script_path),
                str(test_dir / "prompts"),
                str(test_dir / "schemas"),
                str(test_dir / "test_data.json")
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error generating test files: {result.stderr}")
                sys.exit(1)
            else:
                print("Test files generated successfully!")
        else:
            print(f"Generation script not found: {script_path}")
            sys.exit(1)


if __name__ == '__main__':
    # Setup test environment
    setup_test_environment()
    
    # Verify test data is available
    try:
        test_data_loader.data
        print(f"Loaded test data with {len(test_data_loader.get_simple_prompts())} simple prompts, "
              f"{len(test_data_loader.get_structured_prompts())} structured prompts, "
              f"and {len(test_data_loader.get_system_user_prompts())} system/user prompts")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    
    unittest.main(verbosity=2)