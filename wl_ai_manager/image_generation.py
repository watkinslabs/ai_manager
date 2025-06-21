"""
Image generation module for ai_manager.
Provides image generation functionality using Replicate's FLUX PRO.
"""

import io
import logging
import os
from pathlib import Path
from PIL import Image
import replicate

logger = logging.getLogger(__name__)


def create_flux_pro_image(file_name, folder, prompt, file_type="webp", target_width=512, target_height=512, 
                         crop=False, resize=False, client=None, config=None):
    """
    Create an image using FLUX PRO via Replicate API.
    
    Args:
        file_name: Name for the output file
        folder: Folder path where to save the image
        prompt: Text prompt for image generation
        file_type: Output file type (webp, png, jpeg, jpg, bmp)
        target_width: Target width for the image
        target_height: Target height for the image
        crop: Whether to crop the image to exact dimensions
        resize: Whether to resize the image
        client: Replicate client instance
        config: Configuration object with replicate settings
        
    Returns:
        str: Path to saved image or None on failure
    """
    try:
        logger.info(f"Creating image with FLUX PRO: '{prompt[:50]}...'")
        
        aspect_ratios = {
            "1:1": (1, 1),
            "16:9": (16, 9),
            "3:2": (3, 2),
            "2:3": (2, 3),
            "4:5": (4, 5),
            "5:4": (5, 4),
            "9:16": (9, 16),
            "3:4": (3, 4),
            "4:3": (4, 3)
        }
        
        # Calculate aspect ratio
        aspect = target_width / target_height
        closest_ratio = "custom"
        
        for ratio, dims in aspect_ratios.items():
            ratio_value = dims[0] / dims[1]
            if abs(ratio_value - aspect) < 1e-10:
                closest_ratio = ratio
                break
        
        # Get configuration
        replicate_config = config.get('replicate', {}) if config else {}
        
        flux_config = {
            "prompt": prompt,
            "width": target_width,
            "height": target_height,
            "aspect_ratio": closest_ratio,
            "prompt_upsampling": replicate_config.get('prompt_upsampling', True),
            "output_format": replicate_config.get('output_format', 'png'),
            "num_inference_steps": replicate_config.get('num_inference_steps', 50),
            "guidance_scale": replicate_config.get('guidance_scale', 7.5),
        }
        
        # Use provided client or create new one
        if not client:
            if not config or 'replicate' not in config:
                logger.error("No Replicate configuration available")
                return None
            
            api_key = replicate_config.get('api_key')
            if not api_key:
                logger.error("No Replicate API key found in configuration")
                return None
                
            client = replicate.Client(api_token=api_key)
        
        # Get model name from config or use default
        model_name = replicate_config.get('image_model', 'black-forest-labs/flux-pro')
        
        logger.debug(f"Running Replicate model: {model_name}")
        logger.debug(f"FLUX config: {flux_config}")
        
        # Run the model
        output = client.run(
            model_name,
            input=flux_config
        )
        
        # Handle different output types from Replicate
        if hasattr(output, 'read'):
            image_data = output.read()
        elif isinstance(output, str):
            # If output is a URL, download it
            import requests
            response = requests.get(output)
            response.raise_for_status()
            image_data = response.content
        elif isinstance(output, list) and len(output) > 0:
            # Sometimes Replicate returns a list of URLs
            import requests
            response = requests.get(output[0])
            response.raise_for_status()
            image_data = response.content
        else:
            logger.error(f"Unexpected output type from Replicate: {type(output)}")
            return None
        
        # Open image
        image = Image.open(io.BytesIO(image_data))
        logger.info(f"Generated image size: {image.width}x{image.height}")
        
        # Resize if flag is enabled
        if resize:
            current_ratio = image.width / image.height
            target_ratio = target_width / target_height
            
            if current_ratio > target_ratio:
                # Image is too wide, scale by height
                new_height = target_height
                new_width = int(target_height * current_ratio)
            else:
                # Image is too tall, scale by width
                new_width = target_width
                new_height = int(target_width / current_ratio)
            
            logger.debug(f"Resizing image to: {new_width}x{new_height}")
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Crop if flag is enabled
        if crop:
            left = (image.width - target_width) // 2
            top = (image.height - target_height) // 2
            logger.debug(f"Cropping image from ({left}, {top}) to size {target_width}x{target_height}")
            image = image.crop((left, top, left + target_width, top + target_height))
        
        # Validate file type and save image
        valid_file_types = ["png", "jpeg", "jpg", "bmp", "webp"]
        file_type = file_type.lower()
        if file_type not in valid_file_types:
            raise ValueError(f"Unsupported file type: {file_type}. Supported types are: {', '.join(valid_file_types)}")
        
        # Create output directory
        output_dir = Path(folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure correct file extension
        base_name = os.path.splitext(file_name)[0]
        output_path = output_dir / f"{base_name}.{file_type}"
        
        # Convert file type for PIL save
        pil_format = file_type.upper()
        if pil_format == 'JPG':
            pil_format = 'JPEG'
        
        logger.info(f"Saving image to: {output_path}")
        image.save(str(output_path), pil_format)
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Error generating image with FLUX PRO: {e}")
        return None


def init_replicate_client(config):
    """
    Initialize Replicate client using configuration.
    
    Args:
        config: Configuration object with replicate settings
        
    Returns:
        replicate.Client or None on failure
    """
    try:
        if not hasattr(config, 'replicate'):
            logger.error("No 'replicate' section in configuration")
            return None
            
        api_key = config.replicate.get('api_key')
        if not api_key:
            logger.error("No Replicate API key found in configuration")
            return None
            
        client = replicate.Client(api_token=api_key)
        logger.info("Initialized Replicate client successfully")
        return client
        
    except Exception as e:
        logger.error(f"Error initializing Replicate client: {e}")
        return None