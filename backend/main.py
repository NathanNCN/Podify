"""
Podify Backend - Text Extraction and Normalization Service
FastAPI application for extracting and normalizing text from web URLs
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl, Field

from ingestion.url import extract_text_from_url
from parser.extract import TRAFILATURA_AVAILABLE, READABILITY_AVAILABLE
from generation.prompt import generate_podcast_script
from generation.tts import text_to_speech
from generation.summary import generate_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Podify Backend",
    description="Text extraction and normalization service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio storage
# This allows the frontend to access generated audio files
storage_dir = Path(__file__).parent / "storage"
# Ensure storage directory exists (TTS module will create subdirectories)
storage_dir.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")

# Request/Response models
class ExtractRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to extract text from")


class ExtractResponse(BaseModel):
    url: str
    content_type: str
    text: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BatchExtractRequest(BaseModel):
    urls: List[HttpUrl] = Field(..., description="List of URLs to extract text from")
    user_extra_content: Optional[str] = Field(None, description="Optional additional content from the user to include in the podcast")


class BatchExtractResponse(BaseModel):
    results: List[ExtractResponse]
    errors: List[Dict[str, str]]


class CombinedBatchResponse(BaseModel):
    """Combined response with all texts in link1, link2, link3 format"""
    link1: Optional[str] = None
    link2: Optional[str] = None
    link3: Optional[str] = None
    total_characters: int
    script: Optional[str] = None  # Generated podcast script
    summary: Optional[str] = None  # Generated summary with notes and key takeaways
    
    model_config = {"extra": "allow"}  # Allow additional fields for link4, link5, etc. (Pydantic v2)


class GenerateScriptRequest(BaseModel):
    """Request model for generating podcast script from extracted texts"""
    link1: Optional[str] = None
    link2: Optional[str] = None
    link3: Optional[str] = None
    user_extra_content: Optional[str] = Field(None, description="Optional additional content from the user to include in the podcast")
    
    model_config = {"extra": "allow"}  # Allow additional fields for link4, link5, etc.


class GenerateScriptResponse(BaseModel):
    """Response model for generated podcast script"""
    script: str


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech conversion"""
    text: str = Field(..., description="Text to convert to speech")
    voice_id: Optional[str] = Field(None, description="Optional voice ID for ElevenLabs")


class TextToSpeechResponse(BaseModel):
    """Response model for text-to-speech conversion"""
    audio_path: str = Field(..., description="Path to the generated audio file")
    audio_url: str = Field(..., description="URL to access the audio file")


class GenerateSummaryRequest(BaseModel):
    """Request model for generating summary from podcast script"""
    script: str = Field(..., description="Podcast script to summarize")
    user_links: Optional[List[str]] = Field(None, description="Optional list of original source URLs used to generate the podcast")


class GenerateSummaryResponse(BaseModel):
    """Response model for generated summary"""
    summary: str = Field(..., description="Generated summary with notes and key takeaways")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Podify Backend",
        "trafilatura_available": TRAFILATURA_AVAILABLE,
        "readability_available": READABILITY_AVAILABLE
    }


@app.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest):
    """
    Extract clean, normalized text from a single URL.
    
    Process:
    1. Fetch URL content
    2. Extract clean text (removes HTML junk)
    3. Normalize text (removes boilerplate, extra whitespace)
    4. Return structured output
    
    Character limits:
    - Single link: 12,000 characters max
    """
    # Single link: 12k max
    result = extract_text_from_url(request.url, max_length=12000)
    return ExtractResponse(**result)


@app.post("/extract/batch", response_model=CombinedBatchResponse)
async def extract_batch(request: BatchExtractRequest):
    """
    Extract clean, normalized text from multiple URLs in batch.
    
    Returns combined text in format: {link1: text, link2: text, link3: text, total_characters: count}
    
    Character limits based on number of links (total cap: 12,000 characters):
    - 1 link: 12,000 characters max
    - 2 links: 6,000 characters each (12,000 total)
    - 3 links: 4,000 characters each (12,000 total)
    - 4+ links: 3,000 characters each
    """
    errors = []
    
    num_urls = len(request.urls)
    
    # Calculate max_length per URL based on number of links
    # Total cap: 12,000 characters
    if num_urls == 1:
        max_length = 12000
    elif num_urls == 2:
        max_length = 6000  # 6k each = 12k total
    elif num_urls == 3:
        max_length = 4000  # 4k each = 12k total
    else:
        # For 4+ links, use 3k each
        max_length = 3000
    
    # Extract text from all URLs
    texts = {}
    total_characters = 0
    
    for idx, url in enumerate(request.urls, start=1):
        try:
            result = extract_text_from_url(url, max_length=max_length)
            
            # Store text with link key (link1, link2, link3, etc.)
            link_key = f"link{idx}"
            text_content = result.get('text', '')
            texts[link_key] = text_content
            total_characters += len(text_content)
            
        except HTTPException as e:
            errors.append({
                "url": str(url),
                "error": e.detail
            })
            # Store empty string for failed links
            link_key = f"link{idx}"
            texts[link_key] = ""
        except Exception as e:
            errors.append({
                "url": str(url),
                "error": str(e)
            })
            # Store empty string for failed links
            link_key = f"link{idx}"
            texts[link_key] = ""
    
    # Build response with all texts and total character count
    response_data = texts.copy()
    response_data['total_characters'] = total_characters
    
    # Print the combined dictionary for debugging/visibility
    print("\n" + "="*80)
    print("COMBINED BATCH EXTRACTION RESULT")
    print("="*80)
    print(f"Number of URLs processed: {num_urls}")
    print(f"Total characters: {total_characters:,}")
    print(f"Errors encountered: {len(errors)}")
    if errors:
        for error in errors:
            print(f"  - {error['url']}: {error['error']}")
    print("\nCombined Dictionary Format:")
    print("-"*80)
    # Print in the format {link1: "text", link2: "text", ...}
    for key in sorted(texts.keys()):
        text_preview = texts[key][:100] if texts[key] else "(empty)"
        text_length = len(texts[key])
        print(f"{key}: {text_length:,} characters")
        if texts[key]:
            print(f"  Preview: {text_preview}...")
        else:
            print(f"  Status: (empty or failed)")
    print("="*80 + "\n")
    
    # Generate podcast script after all links are parsed
    script = None
    try:
        # Filter out empty links for script generation
        extracted_texts = {k: v for k, v in texts.items() if v and v.strip()}
        
        # Add user extra content if provided
        if request.user_extra_content and request.user_extra_content.strip():
            extracted_texts['user_extra_content'] = request.user_extra_content.strip()
            print(f"User extra content included: {len(request.user_extra_content.strip()):,} characters")
        
        if extracted_texts:
            print("\n" + "="*80)
            print("AUTO-GENERATING PODCAST SCRIPT")
            print("="*80)
            logger.info(f"Auto-generating podcast script from {len(extracted_texts)} source(s)")
            script = generate_podcast_script(extracted_texts)
            response_data['script'] = script
            
            # Auto-generate summary from the script
            try:
                print("\n" + "="*80)
                print("AUTO-GENERATING PODCAST SUMMARY")
                print("="*80)
                logger.info("Auto-generating summary from script")
                # Pass the original URLs and the same extracted_texts used for script generation
                user_links = [str(url) for url in request.urls]
                # Use the same extracted_texts that was used to create the script
                summary = generate_summary(script, user_links, extracted_texts)
                response_data['summary'] = summary
                print("="*80 + "\n")
            except Exception as e:
                logger.error(f"Error auto-generating summary: {e}")
                print(f"\nWARNING: Failed to auto-generate summary: {e}\n")
                # Continue without summary - don't fail the entire request
                response_data['summary'] = None
            
            print("="*80 + "\n")
        else:
            print("\nWARNING: No valid content extracted, skipping script generation\n")
            logger.warning("No valid content extracted, skipping script generation")
    except Exception as e:
        logger.error(f"Error auto-generating script: {e}")
        print(f"\nWARNING: Failed to auto-generate script: {e}\n")
        # Continue without script - don't fail the entire request
        response_data['script'] = None
    
    # Create response object
    response = CombinedBatchResponse(**response_data)
    
    # Also print the actual dictionary format that will be returned
    print("FINAL RESPONSE DICTIONARY (as JSON):")
    print("-"*80)
    # Use model_dump for Pydantic v2, or dict() for v1
    try:
        response_dict = response.model_dump()
    except AttributeError:
        response_dict = response.dict()
    
    # Format it nicely for display
    formatted_dict = "{\n"
    for key in sorted(response_dict.keys()):
        value = response_dict[key]
        if key == 'total_characters':
            formatted_dict += f'  "{key}": {value},\n'
        elif key == 'script' or key == 'summary':
            if value:
                preview = value[:100].replace('\n', '\\n').replace('"', '\\"')
                if len(value) > 100:
                    preview += "..."
                formatted_dict += f'  "{key}": "{preview}" ({len(value):,} chars),\n'
            else:
                formatted_dict += f'  "{key}": null,\n'
        else:
            # Show first 100 chars for preview
            if value:
                preview = value[:100].replace('\n', '\\n').replace('"', '\\"')
                if len(value) > 100:
                    preview += "..."
                formatted_dict += f'  "{key}": "{preview}" ({len(value):,} chars),\n'
            else:
                formatted_dict += f'  "{key}": "",\n'
    formatted_dict = formatted_dict.rstrip(',\n') + "\n}"
    print(formatted_dict)
    print("="*80 + "\n")
    
    return response


@app.post("/generate", response_model=GenerateScriptResponse)
async def generate_script(request: GenerateScriptRequest):
    """
    Generate a podcast script from extracted texts using AI.
    
    Takes the same format as CombinedBatchResponse (link1, link2, link3, etc.)
    and generates a podcast script.
    """
    try:
        print("\n" + "="*80)
        print("GENERATE ENDPOINT CALLED")
        print("="*80)
        print(f"Request received with keys: {list(request.model_dump().keys())}")
        
        # Convert request to dictionary format (exclude non-link fields)
        extracted_texts = {}
        for key, value in request.model_dump().items():
            if key.startswith("link") and value:
                extracted_texts[key] = value
                print(f"  {key}: {len(value):,} characters")
        
        # Add user extra content if provided
        if request.user_extra_content and request.user_extra_content.strip():
            extracted_texts['user_extra_content'] = request.user_extra_content.strip()
            print(f"  user_extra_content: {len(request.user_extra_content.strip()):,} characters")
        
        if not extracted_texts:
            print("ERROR: No valid link content provided")
            raise HTTPException(
                status_code=400,
                detail="No valid link content provided. At least one link with content is required."
            )
        
        print(f"Generating podcast script from {len(extracted_texts)} source(s)...")
        print("="*80 + "\n")
        
        logger.info(f"Generating podcast script from {len(extracted_texts)} source(s)")
        
        # Generate the script
        script = generate_podcast_script(extracted_texts)
        
        logger.info(f"Successfully generated script ({len(script)} characters)")
        
        return GenerateScriptResponse(script=script)
        
    except Exception as e:
        logger.error(f"Error generating podcast script: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate podcast script: {str(e)}"
        )


@app.post("/tts", response_model=TextToSpeechResponse)
async def convert_text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech using ElevenLabs TTS API.
    
    Takes text input and generates an audio file (MP3 format).
    Returns the file path and URL for accessing the audio.
    """
    try:
        logger.info(f"TTS request received: {len(request.text)} characters")
        
        # Call TTS function
        audio_path = text_to_speech(request.text, voice_id=request.voice_id)
        
        # Construct URL for accessing the audio file
        # The path returned is relative to backend root (e.g., "storage/audio/tts/hash.mp3")
        # Convert to URL path by prepending "/"
        audio_url = f"/{audio_path}"
        
        logger.info(f"TTS conversion successful: {audio_path}")
        
        return TextToSpeechResponse(
            audio_path=audio_path,
            audio_url=audio_url
        )
        
    except ValueError as e:
        logger.error(f"TTS validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"TTS conversion error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert text to speech: {str(e)}"
        )


@app.post("/summary", response_model=GenerateSummaryResponse)
async def generate_podcast_summary(request: GenerateSummaryRequest):
    """
    Generate a summary with notes and key takeaways from a podcast script.
    
    This endpoint creates a comprehensive summary document that helps users
    quickly understand the podcast content, especially if they are unable to
    finish listening to the entire episode.
    
    The summary includes:
    - Overview of the podcast
    - Key takeaways
    - Detailed notes by segment
    - Quick reference information
    """
    try:
        logger.info(f"Summary generation request received: {len(request.script)} characters")
        
        if not request.script or not request.script.strip():
            raise HTTPException(
                status_code=400,
                detail="Script cannot be empty"
            )
        
        print("\n" + "="*80)
        print("GENERATING PODCAST SUMMARY")
        print("="*80)
        print(f"Script length: {len(request.script):,} characters")
        if request.user_links:
            print(f"Source links: {len(request.user_links)} link(s)")
            for idx, link in enumerate(request.user_links, 1):
                print(f"  {idx}. {link}")
        print("="*80 + "\n")
        
        # Generate the summary
        summary = generate_summary(request.script, request.user_links)
        
        logger.info(f"Successfully generated summary ({len(summary)} characters)")
        
        return GenerateSummaryResponse(summary=summary)
        
    except ValueError as e:
        logger.error(f"Summary validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
