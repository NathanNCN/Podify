"""
Text extraction module.
Extracts clean text from HTML using trafilatura or readability-lxml.
"""

import logging
from typing import Dict, Any

import httpx

logger = logging.getLogger(__name__)

# Try to import trafilatura (preferred)
try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    logger.warning("trafilatura not available, will use readability-lxml as fallback")

# Try to import readability-lxml (fallback)
try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False
    logger.warning("readability-lxml not available")


def extract_with_trafilatura(url: str) -> Dict[str, Any]:
    """
    Extract text using trafilatura (preferred method).
    Uses trafilatura's built-in fetch_url and extract - no manual HTML parsing.
    
    Returns:
        - raw_html_length: Length of raw HTML (Stage 1)
        - text: Extracted article text (Stage 2)
        - title: Article title
        - metadata: Article metadata
    """
    try:
        # Stage 1: Fetch RAW HTML
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError("Failed to fetch URL content")
        
        raw_html_length = len(downloaded)
        
        # Stage 2: Extract MAIN ARTICLE TEXT from HTML
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
        )
        
        # Get metadata
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata else None
        
        return {
            'raw_html_length': raw_html_length,
            'text': text or '',
            'title': title,
            'metadata': {
                'author': metadata.author if metadata else None,
                'date': str(metadata.date) if metadata and metadata.date else None,
                'site_name': metadata.sitename if metadata else None,
            } if metadata else {}
        }
    except Exception as e:
        logger.error(f"Trafilatura extraction failed: {e}")
        raise


def extract_with_readability(url: str) -> Dict[str, Any]:
    """
    Extract text using readability-lxml (fallback method).
    Uses readability's Document class - no manual HTML parsing.
    
    Returns:
        - raw_html_length: Length of raw HTML (Stage 1)
        - text: Extracted article text (Stage 2)
        - title: Article title
        - metadata: Article metadata
    """
    try:
        # Stage 1: Fetch RAW HTML
        response = httpx.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        
        raw_html_length = len(response.content)
        
        # Stage 2: Extract MAIN ARTICLE TEXT from HTML
        doc = Document(response.content)
        
        # Get cleaned HTML and extract text using readability's built-in methods
        cleaned_html = doc.summary()
        
        # Use readability's text extraction - no manual parsing
        # Readability already handles the HTML parsing internally
        from lxml import html
        tree = html.fromstring(cleaned_html)
        text = tree.text_content()
        
        # Get title
        title = doc.title()
        
        return {
            'raw_html_length': raw_html_length,
            'text': text or '',
            'title': title,
            'metadata': {}
        }
    except Exception as e:
        logger.error(f"Readability extraction failed: {e}")
        raise


def extract_text(url: str) -> Dict[str, Any]:
    """
    Extract text from a URL using the best available method.
    Tries trafilatura first, falls back to readability-lxml if needed.
    
    Args:
        url: URL to extract text from
        
    Returns:
        Dictionary with 'text', 'title', and 'metadata' keys
        
    Raises:
        ImportError: If neither extraction library is available
        Exception: If extraction fails
    """
    if not TRAFILATURA_AVAILABLE and not READABILITY_AVAILABLE:
        raise ImportError("Neither trafilatura nor readability-lxml is available. Please install at least one.")
    
    # Try trafilatura first (preferred)
    if TRAFILATURA_AVAILABLE:
        try:
            return extract_with_trafilatura(url)
        except Exception as e:
            logger.warning(f"Trafilatura failed for {url}, trying readability: {e}")
            if READABILITY_AVAILABLE:
                return extract_with_readability(url)
            else:
                raise
    elif READABILITY_AVAILABLE:
        return extract_with_readability(url)
    else:
        raise ImportError("No extraction library available")

