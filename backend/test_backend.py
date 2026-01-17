"""
Simple test script for the Podify backend.
Run this after starting the server to test the extraction endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_extract(url: str):
    """Test single URL extraction"""
    print(f"Testing extraction for: {url}")
    try:
        response = requests.post(
            f"{BASE_URL}/extract",
            json={"url": url},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Title: {data.get('title', 'N/A')}")
            print(f"Text length: {len(data.get('text', ''))} characters")
            print(f"Text preview (first 200 chars): {data.get('text', '')[:200]}...")
            print(f"Metadata: {json.dumps(data.get('metadata', {}), indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    print()

def test_batch(urls: list):
    """Test batch extraction"""
    print(f"Testing batch extraction for {len(urls)} URLs...")
    try:
        response = requests.post(
            f"{BASE_URL}/extract/batch",
            json={"urls": urls},
            timeout=60
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Successful extractions: {len(data.get('results', []))}")
            print(f"Errors: {len(data.get('errors', []))}")
            for result in data.get('results', []):
                print(f"  - {result['url']}: {len(result.get('text', ''))} chars")
            for error in data.get('errors', []):
                print(f"  - ERROR {error['url']}: {error['error']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Podify Backend Test Script")
    print("=" * 60)
    print()
    
    # Test health check
    test_health_check()
    
    # Test single extraction (using a simple example URL)
    test_extract("https://en.wikipedia.org/wiki/Python_(programming_language)")
    
    # Test batch extraction
    test_batch([
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://en.wikipedia.org/wiki/API"
    ])
    
    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)

