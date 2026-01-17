"""
URL ingestion module.
Orchestrates the process: URL → clean text extraction → normalization → structured output.
"""

import logging
from typing import Dict, Any

from fastapi import HTTPException

from parser.extract import extract_text
from processing.normalize import normalize_text

logger = logging.getLogger(__name__)


def extract_text_from_url(url: str, max_length: int = 50000) -> Dict[str, Any]:
    """
    Extract and normalize text from a URL.
    
    Process:
    1. Fetch URL content
    2. Extract clean text (removes HTML junk)
    3. Normalize text (removes boilerplate, extra whitespace)
    4. Return structured output
    
    Args:
        url: URL string to extract text from
        max_length: Maximum character length for normalized text (default: 50000)
        
    Returns:
        Dictionary with:
        - url: Original URL
        - content_type: Content type (always "text/plain")
        - text: Normalized text content
        - title: Article/page title (if available)
        - metadata: Additional metadata (author, date, site_name, etc.)
        
    Raises:
        HTTPException: If extraction fails or no content is found
    """
    url_str = str(url)
    
    try:
        # Stage 1: Extract text from URL (returns RAW HTML length + MAIN ARTICLE TEXT)
        result = extract_text(url_str)
        
        # Stage 1: RAW HTML
        raw_html_length = result.get('raw_html_length', 0)
        
        # Stage 2: MAIN ARTICLE TEXT (after HTML parsing)
        article_text = result['text']
        article_text_length = len(article_text)
        
        # Stage 3: IMPORTANT INFORMATION ONLY (after normalization)
        normalized_text = normalize_text(article_text, max_length=max_length)
        final_length = len(normalized_text)
        
        # Calculate statistics for each stage
        # Stage 1 → Stage 2: HTML parsing (RAW HTML → MAIN ARTICLE TEXT)
        parsing_removed = raw_html_length - article_text_length
        parsing_percentage = (parsing_removed / raw_html_length * 100) if raw_html_length > 0 else 0
        
        # Stage 2 → Stage 3: Normalization (MAIN ARTICLE TEXT → IMPORTANT INFO)
        normalization_removed = article_text_length - final_length
        normalization_percentage = (normalization_removed / article_text_length * 100) if article_text_length > 0 else 0
        
        # Overall: Stage 1 → Stage 3
        total_removed = raw_html_length - final_length
        total_percentage = (total_removed / raw_html_length * 100) if raw_html_length > 0 else 0
        
        # Extraction statistics removed - only final dictionary/JSON is shown in batch endpoint
        
        if not normalized_text:
            raise HTTPException(
                status_code=400,
                detail="No text content could be extracted from the URL"
            )
        
        return {
            'url': url_str,
            'content_type': 'text/plain',
            'text': normalized_text,
            'title': result.get('title'),
            'metadata': result.get('metadata', {})
        }
    
    except HTTPException:
        raise
    except ImportError as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(
            status_code=500,
            detail="No extraction library available"
        )
    except Exception as e:
        logger.error(f"Error extracting from {url_str}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract content: {str(e)}"
        )

