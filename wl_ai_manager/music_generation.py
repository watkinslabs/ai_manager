"""
Music generation module for ai_manager.
Provides music generation functionality using Replicate's music models.
"""

import io
import logging
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import replicate
from replicate.exceptions import ModelError
import requests
import re

logger = logging.getLogger(__name__)


def create_music(prompt, file_name, folder, duration=30, continuation_audio=None, 
                temperature=1.0, top_k=250, top_p=0, classifier_free_guidance=3,
                output_format="wav", client=None, config=None):
    """
    Create music using Replicate's music generation models.
    
    Args:
        prompt: Text prompt for music generation
        file_name: Name for the output file
        folder: Folder path where to save the music
        duration: Duration in seconds (default 30)
        continuation_audio: Path to audio file to continue from (optional)
        temperature: Generation temperature (default 1.0)
        top_k: Top K sampling parameter (default 250)
        top_p: Top P sampling parameter (default 0)
        classifier_free_guidance: Guidance scale (default 3)
        output_format: Output format (wav or mp3)
        client: Replicate client instance
        config: Configuration object with replicate settings
        
    Returns:
        str: Path to saved audio file or None on failure
    """
    try:
        logger.info(f"Creating music: '{prompt[:50]}...'")
        
        # Get configuration - config IS already ai_manager
        replicate_config = getattr(config, 'replicate', {}) if config else {}
        
        # Build generation parameters
        generation_params = {
            "prompt": prompt[:200] if len(prompt) > 200 else prompt,
            "duration": duration,
            "output_format": output_format,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
            "classifier_free_guidance": classifier_free_guidance,
            "normalization_strategy": "loudness"
        }
        
        # Handle continuation
        audio_file_handle = None
        if continuation_audio and os.path.exists(continuation_audio):
            logger.info(f"Using continuation from: {continuation_audio}")
            generation_params["continuation"] = True
            try:
                audio_file_handle = open(continuation_audio, "rb")
                generation_params["input_audio"] = audio_file_handle
            except Exception as e:
                logger.error(f"Failed to open continuation audio: {e}")
                generation_params["continuation"] = False
        else:
            generation_params["continuation"] = False
            if continuation_audio:
                logger.warning(f"Continuation audio not found: {continuation_audio}")
        
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
        model_name = getattr(replicate_config, 'music_model', 'meta/musicgen')
        
        logger.debug(f"Running Replicate model: {model_name}")
        logger.debug(f"Generation params: {list(generation_params.keys())}")
        
        try:
            # Run the model
            logger.debug("Calling Replicate API for music generation...")
            start_time = time.time()
            
            output = client.run(
                model_name,
                input=generation_params
            )
            
            generation_time = time.time() - start_time
            logger.info(f"Music generation took {generation_time:.2f} seconds")
            
        finally:
            # Always close the file handle
            if audio_file_handle:
                audio_file_handle.close()
        
        # Handle output
        logger.debug(f"Replicate output type: {type(output)}")
        
        # Extract URL from output
        audio_url = None
        if isinstance(output, (list, tuple)) and len(output) > 0:
            audio_url = output[0]
        elif isinstance(output, str) and output.startswith('http'):
            audio_url = output
        elif hasattr(output, '__iter__') and not isinstance(output, (str, bytes)):
            try:
                audio_url = next(iter(output))
            except StopIteration:
                logger.error("Output iterator was empty")
        
        if not audio_url:
            logger.error("No audio URL received from Replicate")
            return None
        
        logger.debug(f"Got audio URL: {audio_url}")
        
        # Download the audio
        logger.info("Downloading generated music...")
        response = requests.get(audio_url, timeout=60, stream=True)
        response.raise_for_status()
        
        # Create output directory
        output_dir = Path(folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save audio file
        file_extension = output_format.lower()
        if file_extension not in ['wav', 'mp3']:
            file_extension = 'wav'
        
        output_path = output_dir / f"{file_name}.{file_extension}"
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Successfully saved music: {output_path}")
        return str(output_path)
        
    except ModelError as e:
        logger.error(f"Replicate model error: {e}")
        if hasattr(e, 'args') and e.args:
            err = e.args[0]
            if hasattr(err, 'status'):
                logger.error(f"Status: {err.status}, Error: {err.error}")
                if hasattr(err, 'logs'):
                    logger.error(f"Model logs: {err.logs}")
        return None
    except Exception as e:
        logger.error(f"Error generating music: {e}")
        logger.exception("Full traceback:")
        return None


def create_music_continuation_chain(prompts, folder, base_file_name="music", 
                                  duration=30, client=None, config=None):
    """
    Generate a chain of music continuations from a list of prompts.
    Each generation continues from the previous one.
    
    Args:
        prompts: List of text prompts for music generation
        folder: Folder path where to save the music files
        base_file_name: Base name for output files
        duration: Duration for each segment
        client: Replicate client instance
        config: Configuration object
        
    Returns:
        List of generated file paths
    """
    logger.info(f"Starting music continuation chain with {len(prompts)} prompts")
    
    generated_files = []
    last_audio = None
    
    for i, prompt in enumerate(prompts):
        logger.info(f"\nGenerating segment {i+1}/{len(prompts)}")
        logger.info(f"Prompt: {prompt[:80]}...")
        
        file_name = f"{base_file_name}_{i:03d}"
        
        result = create_music(
            prompt=prompt,
            file_name=file_name,
            folder=folder,
            duration=duration,
            continuation_audio=last_audio,
            client=client,
            config=config
        )
        
        if result:
            generated_files.append(result)
            last_audio = result
            logger.info(f"✓ Segment {i+1} generated successfully")
        else:
            logger.error(f"✗ Failed to generate segment {i+1}")
            # Continue with the last successful audio if available
        
        # Add delay between generations to avoid rate limiting
        if i < len(prompts) - 1:
            time.sleep(2)
    
    logger.info(f"\nChain complete: {len(generated_files)}/{len(prompts)} segments generated")
    return generated_files


def create_music_variations(base_prompt, variation_prompts, folder, base_file_name="variation",
                          duration=30, client=None, config=None):
    """
    Generate variations of music based on a base prompt with modifications.
    
    Args:
        base_prompt: Base music prompt
        variation_prompts: List of variation descriptions to append
        folder: Output folder
        base_file_name: Base name for files
        duration: Duration for each variation
        client: Replicate client
        config: Configuration
        
    Returns:
        List of generated file paths
    """
    logger.info(f"Generating {len(variation_prompts)} variations of base prompt")
    
    generated_files = []
    
    for i, variation in enumerate(variation_prompts):
        full_prompt = f"{base_prompt}, {variation}"
        file_name = f"{base_file_name}_{i:03d}"
        
        logger.info(f"\nVariation {i+1}: {variation}")
        
        result = create_music(
            prompt=full_prompt,
            file_name=file_name,
            folder=folder,
            duration=duration,
            client=client,
            config=config
        )
        
        if result:
            generated_files.append(result)
            logger.info(f"✓ Variation {i+1} generated")
        else:
            logger.error(f"✗ Failed variation {i+1}")
        
        # Delay between generations
        if i < len(variation_prompts) - 1:
            time.sleep(2)
    
    return generated_files


def save_music_metadata(file_path, prompt, duration, continuation_from=None, metadata=None):
    """
    Save metadata for generated music file.
    
    Args:
        file_path: Path to the music file
        prompt: Generation prompt
        duration: Duration in seconds
        continuation_from: Previous file if continuation
        metadata: Additional metadata dict
    """
    meta = {
        'prompt': prompt,
        'duration': duration,
        'generated_at': datetime.now().isoformat(),
        'continuation_from': continuation_from,
        'file_path': file_path
    }
    
    if metadata:
        meta.update(metadata)
    
    # Save as JSON next to the audio file
    metadata_path = Path(file_path).with_suffix('.json')
    
    with open(metadata_path, 'w') as f:
        json.dump(meta, f, indent=2)
    
    logger.debug(f"Saved metadata to: {metadata_path}")