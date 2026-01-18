"""
Summary generation module for creating podcast summaries with notes and key takeaways.
"""

import logging
import os
import time
from typing import Dict, Optional, List
from pathlib import Path

from google import genai
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


def create_summary_prompt(script: str, user_links: Optional[List[str]] = None, extracted_texts: Optional[Dict[str, str]] = None) -> str:
    """
    Create a prompt for generating a summary with notes and key takeaways from a podcast script.
    
    Args:
        script: The generated podcast script text
        user_links: Optional list of original source URLs used to generate the podcast
        extracted_texts: Optional dictionary with the same content used to create the script
                        (includes link1, link2, etc. and optionally user_extra_content)
        
    Returns:
        Formatted prompt string for AI generation
    """
    # Build source links section if provided
    source_links_section = ""
    if user_links and len(user_links) > 0:
        links_list = "\n".join([f"- {link}" for link in user_links])
        source_links_section = f"""
    SOURCE LINKS:
    This podcast was generated from the following source(s):
    {links_list}

"""
    
    # Build source content section using the same format as script generation
    source_content_section = ""
    if extracted_texts and len(extracted_texts) > 0:
        content_sections = []
        user_extra_content = None
        
        # Process content in the same order as script generation
        for key in sorted(extracted_texts.keys()):
            # Handle user extra content separately
            if key == "user_extra_content" and extracted_texts[key]:
                user_extra_content = extracted_texts[key]
                continue
            # Skip non-link keys like "total_characters"
            if key.startswith("link") and extracted_texts[key] and extracted_texts[key].strip():
                link_num = key.replace("link", "")
                content = extracted_texts[key]
                # Limit each source to reasonable length for prompt (keep more than before since it's important)
                if len(content) > 3000:
                    content = content[:3000] + "\n[... content truncated for prompt ...]"
                content_sections.append(f"## Source {link_num}\n{content}\n")
        
        # Add user extra content if provided (same priority as in script generation)
        if user_extra_content:
            content_preview = user_extra_content
            if len(user_extra_content) > 3000:
                content_preview = user_extra_content[:3000] + "\n[... content truncated for prompt ...]"
            content_sections.insert(0, f"## Additional User Content (PRIORITY - This content was given high priority in script generation)\n{content_preview}\n")
        
        if content_sections:
            source_content_section = f"""
    SOURCE CONTENT USED TO CREATE THE SCRIPT:
    Below is the original source content that was used to generate this podcast script. This includes parsed content from the source links and any additional user-provided content:
    
    {chr(10).join(content_sections)}
"""
    
    prompt = f"""You are creating a comprehensive summary document for a podcast script. This summary will help users quickly understand the podcast content, especially if they are unable to finish listening to the entire episode.
{source_links_section}{source_content_section}
    PODCAST SCRIPT:
    {script}

    YOUR TASK:
    Create a well-structured summary document that includes:

    1. OVERVIEW SECTION:
    - Write 2-3 sentences summarizing what the podcast covers
    - Identify the main topic and theme
    - Note the target audience or context

    2. KEY TAKEAWAYS SECTION:
    - Extract 5-8 most important insights or lessons from the podcast
    - Each takeaway should be:
        * Clear and actionable
        * Standalone (understandable without additional context)
        * Specific rather than generic
    - Format with bold headers and 1-2 sentence explanations

    3. DETAILED NOTES SECTION:
    - Break down the podcast into logical segments based on topic shifts
    - For each segment, provide:
        * Topic/theme heading
        * Main points discussed
        * Important examples, statistics, or quotes
        * Any actionable advice or insights
    - Use clear markdown headings (### for segment titles)

    4. QUICK REFERENCE SECTION:
    - List important statistics or numbers mentioned
    - Include key quotes or memorable phrases
    - Note resources or concepts highlighted
    - Record any calls-to-action or next steps

    FORMATTING REQUIREMENTS:
    - Use markdown formatting (## for main sections, ### for subsections, ** for bold)
    - Use bullet points and numbered lists for readability
    - Keep language concise but informative
    - Make it scannable so users can quickly find information
    - Preserve important details like numbers, names, and specific examples

    TONE:
    - Match the podcast's tone (professional, casual, educational, etc.)
    - Be helpful and informative
    - Write clearly and accessibly
    """
    return prompt


def generate_summary(script: str, user_links: Optional[List[str]] = None, extracted_texts: Optional[Dict[str, str]] = None) -> str:
    """
    Generate a summary with notes and key takeaways from a podcast script using Gemini API.
    
    Args:
        script: The podcast script text to summarize
        user_links: Optional list of original source URLs used to generate the podcast
        extracted_texts: Optional dictionary with the same content used to create the script
                        (includes link1, link2, etc. and optionally user_extra_content)
        
    Returns:
        Generated summary with notes and key takeaways
    """
    if not script or not script.strip():
        raise ValueError("Script cannot be empty")
    
    # Initialize the Gemini client
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    
    # Create the prompt
    prompt = create_summary_prompt(script, user_links, extracted_texts)
    
    # Use current production-ready models (as of 2025)
    # Gemini 1.5 models are retired, using Gemini 2.5 series
    model_names = [
        'gemini-2.5-flash',      # Stable, price/performance balanced
        'gemini-2.5-flash-lite', # Fastest and most cost-efficient
        'gemini-2.5-pro',        # Top-tier for complex prompts
    ]
    
    # Generate the summary
    last_error = None
    response = None
    for model_name in model_names:
        try:
            logger.info(f"Trying model: {model_name}")
            logger.info("Calling Gemini API to generate podcast summary...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "temperature": 0.5,  # Lower temperature for more focused summaries
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 2000,  # Enough for comprehensive summary
                }
            )
            # If we get here, the model worked
            logger.info(f"Successfully used model: {model_name}")
            break
        except Exception as e:
            error_str = str(e)
            last_error = e
            
            # Handle rate limit errors with wait
            if "429" in error_str or "quota" in error_str.lower():
                logger.warning(f"Rate limit hit for {model_name}. Waiting 10 seconds before trying next model...")
                time.sleep(10)
            else:
                logger.warning(f"Model {model_name} failed: {e}")
            
            continue
    else:
        # If all models failed, raise the last error
        if last_error:
            raise last_error
        else:
            raise Exception("No models available and no error captured")
    
    # Access the text from response
    # The new API returns response.text directly
    summary_text = response.text if hasattr(response, 'text') else str(response)
    
    logger.info(f"Summary generated successfully, length: {len(summary_text)} characters")
    
    # Display the generated summary in a formatted way
    import sys
    sys.stdout.flush()  # Ensure previous output is flushed
    
    print("\n" + "="*80, flush=True)
    print("GENERATED PODCAST SUMMARY", flush=True)
    print("="*80, flush=True)
    print(f"Summary length: {len(summary_text):,} characters", flush=True)
    word_count = len(summary_text.split())
    print(f"Estimated word count: ~{word_count:,} words", flush=True)
    print("\n" + "-"*80, flush=True)
    print("SUMMARY CONTENT:", flush=True)
    print("-"*80, flush=True)
    print(summary_text, flush=True)
    print("="*80 + "\n", flush=True)
    
    sys.stdout.flush()  # Final flush
    
    return summary_text

