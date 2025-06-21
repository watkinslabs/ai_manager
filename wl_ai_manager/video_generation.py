"""
Video generation module for ai_manager.
Provides video generation functionality using Google's VEO-2 via Replicate.
"""

import io
import logging
import os
import time
from pathlib import Path
import replicate
import requests

logger = logging.getLogger(__name__)


def create_veo_video(prompt, file_name, folder, duration=5, aspect_ratio="16:9", 
                     client=None, config=None, data_url=None):
    """
    Create a video using Google VEO-2 via Replicate API.
    
    Args:
        prompt: Text prompt for video generation
        file_name: Name for the output file
        folder: Folder path where to save the video
        duration: Video duration in seconds (5, 10, 15, 20)
        aspect_ratio: Video aspect ratio ("16:9", "9:16", "1:1", "4:3", "3:4")
        client: Replicate client instance
        config: Configuration object with replicate settings
        data_url: Base URL for serving local files to Replicate
        
    Returns:
        str: Path to saved video or None on failure
    """
    try:
        logger.info(f"Creating video with VEO-2: '{prompt[:50]}...'")
        
        # Get configuration - config IS already ai_manager
        replicate_config = getattr(config, 'replicate', {}) if config else {}
        
        # Get data URL from config if not provided
        if not data_url and replicate_config:
            data_url = getattr(replicate_config, 'data_url', None)
        
        # Validate duration
        valid_durations = [5, 10, 15, 20]
        if duration not in valid_durations:
            logger.warning(f"Invalid duration {duration}, using 5 seconds")
            duration = 5
        
        # Validate aspect ratio
        valid_ratios = ["16:9", "9:16", "1:1", "4:3", "3:4"]
        if aspect_ratio not in valid_ratios:
            logger.warning(f"Invalid aspect ratio {aspect_ratio}, using 16:9")
            aspect_ratio = "16:9"
        
        # VEO-2 configuration
        veo_config = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio
        }
        
        # Use provided client or create new one
        if not client:
            if not config or not hasattr(config, 'replicate'):
                logger.error("No replicate configuration available")
                return None
            
            replicate_config = config.replicate
            api_key = getattr(replicate_config, 'api_key', None)
            
            if not api_key:
                logger.error("No Replicate API key found in configuration")
                return None
                
            client = replicate.Client(api_token=api_key)
        
        # Get model name from config or use default
        model_name = getattr(replicate_config, 'video_model', 'google/veo-2')
        
        logger.debug(f"Running Replicate model: {model_name}")
        logger.debug(f"VEO config: {veo_config}")
        
        # Run the model
        logger.debug("Calling Replicate API for video generation...")
        start_time = time.time()
        
        output = client.run(
            model_name,
            input=veo_config
        )
        
        generation_time = time.time() - start_time
        logger.info(f"Video generation took {generation_time:.2f} seconds")
        
        # Log the output type for debugging
        logger.debug(f"Replicate output type: {type(output)}")
        logger.debug(f"Replicate output: {output}")
        
        # Handle different output types from Replicate
        video_url = None
        
        # Check if output is a FileOutput object
        if hasattr(output, 'read'):
            logger.debug("Output has read method, reading directly")
            video_data = output.read()
        # Check if it's a generator or iterator
        elif hasattr(output, '__iter__') and not isinstance(output, (str, bytes)):
            logger.debug("Output is iterable, getting first item")
            try:
                # Get the first item from the iterator
                first_item = next(iter(output))
                logger.debug(f"First item type: {type(first_item)}, value: {first_item}")
                
                if isinstance(first_item, str) and first_item.startswith('http'):
                    video_url = first_item
                else:
                    logger.error(f"Unknown item type in iterator: {type(first_item)}")
                    return None
            except StopIteration:
                logger.error("Iterator was empty")
                return None
        elif isinstance(output, str) and output.startswith('http'):
            video_url = output
        elif isinstance(output, list) and len(output) > 0:
            first_item = output[0]
            if isinstance(first_item, str) and first_item.startswith('http'):
                video_url = first_item
        else:
            logger.error(f"Unexpected output type from Replicate: {type(output)}")
            return None
        
        # Download video if we have a URL
        if video_url:
            logger.debug(f"Downloading video from URL: {video_url}")
            response = requests.get(video_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Create output directory
            output_dir = Path(folder)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save video file
            output_path = output_dir / f"{file_name}.mp4"
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully saved video: {output_path}")
            return str(output_path)
        else:
            logger.error("No video URL received from Replicate")
            return None
        
    except replicate.exceptions.ReplicateError as e:
        logger.error(f"Replicate API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error generating video with VEO-2: {e}")
        logger.exception("Full traceback:")
        return None


def create_veo_video_from_image(image_path, prompt, file_name, folder, duration=5, 
                               aspect_ratio="16:9", client=None, config=None, data_url=None):
    """
    Create a video from an image using VEO-2 (if supported) or fallback to prompt-only.
    
    Note: VEO-2 may not support image inputs directly. This function is prepared
    for when/if image conditioning becomes available.
    
    Args:
        image_path: Path to input image
        prompt: Text prompt for video generation
        file_name: Name for the output file
        folder: Folder path where to save the video
        duration: Video duration in seconds
        aspect_ratio: Video aspect ratio
        client: Replicate client instance
        config: Configuration object
        data_url: Base URL for serving files
        
    Returns:
        str: Path to saved video or None on failure
    """
    logger.info(f"Creating video from image: {image_path}")
    
    # Check if image exists
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return None
    
    # Get data URL from config if not provided
    if not data_url and config:
        replicate_config = getattr(config, 'replicate', {}) if config else {}
        data_url = getattr(replicate_config, 'data_url', None)
    
    if data_url:
        # Construct URL for the image
        image_filename = os.path.basename(image_path)
        image_url = f"{data_url.rstrip('/')}/{image_filename}"
        logger.info(f"Image URL would be: {image_url}")
        
        # Note: VEO-2 currently doesn't support image inputs
        # This is prepared for future updates
        logger.warning("VEO-2 doesn't currently support image inputs. Using prompt-only generation.")
    
    # For now, just use the prompt
    return create_veo_video(
        prompt=prompt,
        file_name=file_name,
        folder=folder,
        duration=duration,
        aspect_ratio=aspect_ratio,
        client=client,
        config=config,
        data_url=data_url
    )


def init_replicate_client_for_video(config):
    """
    Initialize Replicate client for video generation.
    
    Args:
        config: Configuration object (ai_manager config with replicate settings)
        
    Returns:
        replicate.Client or None on failure
    """
    try:
        if not hasattr(config, 'replicate'):
            logger.error("No 'replicate' section in configuration")
            return None
            
        replicate_config = config.replicate
        api_key = getattr(replicate_config, 'api_key', None)
        
        if not api_key:
            logger.error("No Replicate API key found in configuration")
            return None
            
        client = replicate.Client(api_token=api_key)
        logger.info("Initialized Replicate client for video generation")
        return client
        
    except Exception as e:
        logger.error(f"Error initializing Replicate client: {e}")
        return None