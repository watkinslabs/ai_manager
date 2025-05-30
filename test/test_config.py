"""
Test configuration for AI Manager using config.yaml
"""

import tempfile
import os
from pathlib import Path

def get_test_config():
    """Load configuration from config.yaml using WL_CONFIG_MANAGER"""
    try:
        from wl_config_manager import ConfigManager
    except ImportError:
        raise ImportError("WL_CONFIG_MANAGER not found. Install with: pip install wl-config-manager")
    
    # Load config using WL_CONFIG_MANAGER
    config = ConfigManager("config.yaml")
    config=config.ai_manager
    
    # Create test directories
    test_base_dir = Path(__file__).parent / "test_data"
    test_base_dir.mkdir(exist_ok=True)
    
    prompts_dir = test_base_dir / "prompts"
    schemas_dir = test_base_dir / "schemas"
    output_dir = test_base_dir / "output"
    temp_dir = test_base_dir / "temp"
    
    prompts_dir.mkdir(exist_ok=True)
    schemas_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    temp_dir.mkdir(exist_ok=True)
    
    # Override config paths for testing
    config.prompt_folder = str(prompts_dir)
    config.schema_folder = str(schemas_dir)
    config.output_dir = str(output_dir)
    config.temp_dir = str(temp_dir)
    
    return config

