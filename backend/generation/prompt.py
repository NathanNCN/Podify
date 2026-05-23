"""
Prompt generation module for creating podcast scripts from extracted content.
"""

import logging
import os
import time
from typing import Dict
from pathlib import Path

from google import genai
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


def create_podcast_prompt(extracted_texts: Dict[str, str]) -> str:
    """
    Create a prompt for generating a podcast script from extracted texts.
    
    Args:
        extracted_texts: Dictionary with keys like "link1", "link2", "link3" 
                        containing the extracted text content
        
    Returns:
        Formatted prompt string for AI generation
    """
    # Build the content sections
    content_sections = []
    user_extra_content = None
    
    for key in sorted(extracted_texts.keys()):
        # Handle user extra content separately
        if key == "user_extra_content" and extracted_texts[key]:
            user_extra_content = extracted_texts[key]
            continue
        # Skip non-link keys like "total_characters"
        if key.startswith("link") and extracted_texts[key]:
            link_num = key.replace("link", "")
            content_sections.append(f"## Source {link_num}\n{extracted_texts[key]}\n")
    
    # Add user extra content if provided (prioritize it by placing it first or with special emphasis)
    if user_extra_content:
        # Place user content at the beginning to give it priority
        content_sections.insert(0, f"## Additional User Content (PRIORITY - Integrate this content prominently)\n{user_extra_content}\n")
    
    # Combine all content
    combined_content = "\n".join(content_sections)
    
    # Build user content instruction if present
    user_content_instruction = ""
    if user_extra_content:
        user_content_instruction = """
IMPORTANT - USER CONTENT INTEGRATION:
- The "Additional User Content" section contains content directly provided by the user
- This content should be given HIGH PRIORITY and integrated prominently throughout the script
- Use the user's content to guide the narrative, add personal context, or emphasize specific points
- Seamlessly weave user content into the script rather than treating it as separate
- If user content provides context or preferences, use it to shape how you present the source material
"""
    
    # Create the prompt with f-string to substitute the combined_content
    prompt = f"""You are a professional podcast script writer creating audio content for listeners who are driving or multitasking.

CONTENT TO USE:
{combined_content}

YOUR TASK:
Create a 10-12 minute podcast script (approximately 1,500-1,800 words when spoken aloud) that:

NOTE: Here is the user content that you should use to guide the script:
{user_content_instruction}

CONTENT HANDLING:
- Extract the 5-8 most important insights from the sources
- If sources conflict, acknowledge both perspectives briefly
- Prioritize actionable takeaways and concrete examples over theory
- Combine related points from multiple sources into unified segments
- If user content is provided, ensure it is prominently featured and integrated throughout the script

STRUCTURE:
- Start with a compelling hook or question
- Briefly preview what listeners will learn
- Set expectations for length

[MAIN SEGMENTS] 
- Break content into 3-5 distinct segments
- Each segment covers one major theme or idea
- Use clear transitions between segments ("Now let's talk about...")
- Include specific examples, stats, or quotes to maintain interest

[CONCLUSION] 
- Summarize 3 key takeaways
- End with a thought-provoking question or call-to-action

WRITING STYLE:
- Conversational and warm, like talking to a friend
- Short sentences and paragraphs (listeners can't re-read)
- Never reference visuals ("as shown in the chart")
- Use "you" to engage listeners directly
- Include natural pauses with [PAUSE] markers where appropriate
- Add emphasis notes in parentheses: (enthusiastically), (slow down for emphasis)

AVOID:
- Filler phrases like "In conclusion" or "As we discussed"
- Lists with more than 3 items (hard to follow by ear)
- Complex jargon without explanation
- Assuming listeners can take notes
IMPORTANT RULES:
-DO NOT include any section headers or titles in the script.
-DO NOT include any markdown or other formatting in the script.
-DO NOT include any section headers or titles in the script.
-JUST GENERATE THE SCRIPT, NO OTHER TEXT. As if it was a pargraph.
Generate the podcast script now:
"""
    return prompt


def generate_podcast_script(extracted_texts: Dict[str, str]) -> str:
    """
    Generate a podcast script using Gemini API.
    
    Args:
        extracted_texts: Dictionary with extracted text content from links
        
    Returns:
        Generated podcast script
    """
    # Initialize the Gemini client
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    
    # Create the prompt
    prompt = create_podcast_prompt(extracted_texts)
    
    # Use current production-ready models (as of 2025)
    # Gemini 1.5 models are retired, using Gemini 2.5 series
    model_names = [
        'gemini-2.5-flash',      # Stable, price/performance balanced
        'gemini-2.5-flash-lite', # Fastest and most cost-efficient
        'gemini-2.5-pro',        # Top-tier for complex prompts
    ]
    
    # Generate the script
    last_error = None
    response = None
    for model_name in model_names:
        try:
            logger.info(f"Trying model: {model_name}")
            logger.info("Calling Gemini API to generate podcast script...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "temperature": 0.7,  # Balance creativity and coherence
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 3000,  # Enough for ~1800 word script
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
    script_text = response.text if hasattr(response, 'text') else str(response)
    
    logger.info(f"Script generated successfully, length: {len(script_text)} characters")
    
    # Display the generated script in a formatted way
    import sys
    sys.stdout.flush()  # Ensure previous output is flushed
    
    print("\n" + "="*80, flush=True)
    print("GENERATED PODCAST SCRIPT", flush=True)
    print("="*80, flush=True)
    print(f"Script length: {len(script_text):,} characters", flush=True)
    word_count = len(script_text.split())
    print(f"Estimated word count: ~{word_count:,} words", flush=True)
    duration = word_count / 150.0 if word_count > 0 else 0
    print(f"Estimated duration: ~{duration:.1f} minutes (at 150 words/min)", flush=True)
    print("\n" + "-"*80, flush=True)
    print("SCRIPT CONTENT:", flush=True)
    print("-"*80, flush=True)
    print(script_text, flush=True)
    print("="*80 + "\n", flush=True)
    
    sys.stdout.flush()  # Final flush
    
    return script_text