"""
Text-to-Speech (TTS) module using ElevenLabs API.

Design Choices:
- Separation of concerns: TTS API logic is separate from file storage operations
- Deterministic filenames: Uses SHA-256 hash of input text to ensure same text 
  generates same filename (enables caching/reuse)
- Storage location: Centralized in storage/audio/tts/ relative to backend root
- Error handling: Distinguishes between API failures and file system failures
- Environment-based config: API key loaded from ELEVENLABS_API_KEY env var
- Format: Uses MP3 for smaller file sizes and broad compatibility
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

# Load environment variables from .env file (same pattern as prompt.py)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# Configuration constants
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
AUDIO_STORAGE_DIR = Path(__file__).parent.parent / "storage" / "audio" / "tts"
AUDIO_FORMAT = "mp3"  # MP3 for smaller file sizes and broad compatibility


def _ensure_storage_directory() -> Path:
    """
    Ensure the audio storage directory exists, creating it if necessary.
    
    Returns:
        Path object pointing to the storage directory
    """
    AUDIO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    return AUDIO_STORAGE_DIR


def _generate_filename(text: str) -> str:
    """
    Generate a deterministic filename based on the input text hash.
    
    Uses SHA-256 hash to ensure same text always produces same filename,
    enabling caching and avoiding duplicate API calls for identical content.
    
    Args:
        text: Input text to hash
        
    Returns:
        Filename string (without extension)
    """
    # Create hash of text content for deterministic filename
    text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    return text_hash


def _call_elevenlabs_api(text: str, api_key: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> bytes:
    """
    Call ElevenLabs TTS API to generate audio from text.
    
    Args:
        text: Text content to convert to speech
        api_key: ElevenLabs API key
        voice_id: Voice ID to use (default: Rachel - balanced voice)
        
    Returns:
        Audio data as bytes (MP3 format)
        
    Raises:
        httpx.HTTPStatusError: If API request fails
        httpx.RequestError: If network/request error occurs
    """
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",  # Fast, free tier compatible model
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    # Make API request with timeout
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{ELEVENLABS_API_URL}/{voice_id}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx
        return response.content


def _save_audio_file(audio_data: bytes, filename: str) -> Path:
    """
    Save audio data to disk with the specified filename.
    
    Args:
        audio_data: Audio bytes to save
        filename: Filename (without extension) to use
        
    Returns:
        Path object pointing to the saved file
        
    Raises:
        OSError: If file write operation fails
    """
    file_path = AUDIO_STORAGE_DIR / f"{filename}.{AUDIO_FORMAT}"
    
    try:
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        logger.info(f"Audio file saved: {file_path}")
        return file_path
    except OSError as e:
        logger.error(f"Failed to save audio file: {e}")
        raise


def text_to_speech(text: str, voice_id: Optional[str] = None) -> str:
    """
    Convert text to speech using ElevenLabs API and save to disk.
    
    This function orchestrates the TTS pipeline:
    1. Validates input and API key
    2. Generates deterministic filename from text hash
    3. Checks if file already exists (caching)
    4. Calls ElevenLabs API if needed
    5. Saves audio file to storage directory
    6. Returns file path as string
    
    Args:
        text: Text content to convert to speech
        voice_id: Optional voice ID (default: "21m00Tcm4TlvDq8ikWAM" - Rachel)
        
    Returns:
        File path string to the generated audio file (relative to backend root)
        
    Raises:
        ValueError: If text is empty or API key is missing
        httpx.HTTPStatusError: If ElevenLabs API request fails
        httpx.RequestError: If network/request error occurs
        OSError: If file write operation fails
    """
    # Validate input
    if not text or not text.strip():
        raise ValueError("Text input cannot be empty")
    
    # Get API key from environment
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        env_file_path = Path(__file__).parent.parent / '.env'
        raise ValueError(
            "ELEVENLABS_API_KEY environment variable is required.\n"
            f"Create a .env file at: {env_file_path}\n"
            "Add the following line:\n"
            "ELEVENLABS_API_KEY=your_api_key_here\n\n"
            "Get your API key from: https://elevenlabs.io/app/api-keys"
        )
    
    # Use default voice if not specified
    if voice_id is None:
        voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - balanced, professional voice
    
    # Ensure storage directory exists
    _ensure_storage_directory()
    
    # Generate deterministic filename
    filename = _generate_filename(text)
    file_path = AUDIO_STORAGE_DIR / f"{filename}.{AUDIO_FORMAT}"
    
    # Check if file already exists (caching - same text = same file)
    if file_path.exists():
        logger.info(f"Audio file already exists, returning cached: {file_path}")
        return str(file_path.relative_to(Path(__file__).parent.parent))
    
    # Call ElevenLabs API
    try:
        logger.info(f"Calling ElevenLabs API for text-to-speech conversion...")
        audio_data = _call_elevenlabs_api(text, api_key, voice_id)
        logger.info(f"Successfully received audio data ({len(audio_data)} bytes)")
    except httpx.HTTPStatusError as e:
        logger.error(f"ElevenLabs API error: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.RequestError as e:
        logger.error(f"Network error calling ElevenLabs API: {e}")
        raise
    
    # Save audio file to disk
    try:
        saved_path = _save_audio_file(audio_data, filename)
        # Return relative path from backend root for easier use
        return str(saved_path.relative_to(Path(__file__).parent.parent))
    except OSError as e:
        logger.error(f"Failed to save audio file: {e}")
        raise

