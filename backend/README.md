# Podify Backend

Python backend service for extracting and normalizing text from web URLs.

## Features

- **Text Extraction**: Uses `trafilatura` (preferred) or `readability-lxml` (fallback) to extract clean text from web pages
- **Text Normalization**: Removes boilerplate, extra whitespace, and common web page clutter
- **Structured Output**: Returns clean, normalized text with metadata (title, author, date, etc.)
- **Batch Processing**: Supports extracting text from multiple URLs at once

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the `backend/` directory with the following:
```bash
# ElevenLabs API Key (required for text-to-speech)
# Get your API key from: https://elevenlabs.io/app/api-keys
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Google Gemini API Key (required for script generation)
GOOGLE_API_KEY=your_google_api_key_here
```

## Running the Server

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST `/extract`
Extract text from a single URL.

**Request:**
```json
{
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "url": "https://example.com/article",
  "content_type": "text/plain",
  "text": "Normalized, clean text content...",
  "title": "Article Title",
  "metadata": {
    "author": "Author Name",
    "date": "2024-01-01",
    "site_name": "Example Site"
  }
}
```

### POST `/extract/batch`
Extract text from multiple URLs.

**Request:**
```json
{
  "urls": [
    "https://example.com/article1",
    "https://example.com/article2"
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "url": "https://example.com/article1",
      "content_type": "text/plain",
      "text": "Normalized text...",
      "title": "Article 1"
    }
  ],
  "errors": [
    {
      "url": "https://example.com/article2",
      "error": "Error message"
    }
  ]
}
```

### GET `/`
Health check endpoint.

## Text Normalization

The service normalizes extracted text by:
- Removing extra whitespace (multiple spaces, tabs, newlines)
- Removing common boilerplate patterns (cookie notices, social media prompts, etc.)
- Removing URLs and email addresses
- Cleaning up text structure
- Filtering out very short lines (likely navigation/boilerplate)

## Dependencies

- **FastAPI**: Modern web framework for building APIs
- **trafilatura**: Best-in-class text extraction library (preferred)
- **readability-lxml**: Fallback text extraction library
- **httpx**: HTTP client for fetching web pages
- **lxml**: XML/HTML parsing library
