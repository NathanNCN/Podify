"""
Text normalization module for podcast script generation.
Removes boilerplate, navigation, and visual-only elements while preserving
main narrative content, facts, quotes, headings, and context.
"""

import re
import logging

logger = logging.getLogger(__name__)


def normalize_text(text: str, max_length: int = 50000) -> str:
    """
    Normalize extracted text for podcast script generation.
    
    Removes:
    - Navigation elements (menus, breadcrumbs, "click here")
    - Visual-only elements ("see image below", "chart shows", image captions)
    - Hyperlinks and URLs
    - Author bios, comment sections, related articles
    - Formatting instructions (bold, italics markers)
    - Metadata (publish dates, tags, categories unless core to story)
    
    Keeps:
    - Main narrative content
    - Key facts, statistics, quotes
    - Section headings
    - Important context (who, what, when, where, why)
    - Explanations and examples
    
    Args:
        text: Raw extracted text from HTML
        max_length: Maximum character length for the normalized text (default: 50000)
        
    Returns:
        Normalized text suitable for podcast script generation
    """
    if not text:
        return ""
    
    # Step 1: Remove URLs and hyperlinks
    # Remove full URLs (http://, https://, www.)
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'www\.[^\s]+', '', text)
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    
    # Step 2: Remove navigation and UI elements
    navigation_patterns = [
        r'\bclick here\b',
        r'\bclick to [^\s]+',
        r'\bread more\b',
        r'\bcontinue reading\b',
        r'\bnext page\b',
        r'\bprevious page\b',
        r'\bhome\b.*?menu',
        r'\bnavigation\b',
        r'\bmenu\b',
        r'\bbreadcrumb\b',
        r'\bskip to [^\s]+',
        r'\bback to top\b',
        r'\bshare on [^\s]+',
        r'\bfollow us on [^\s]+',
        r'\bsubscribe\b.*?newsletter',
        r'\bsign up\b.*?newsletter',
    ]
    for pattern in navigation_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Step 3: Remove visual-only elements
    visual_patterns = [
        r'see image below',
        r'see image above',
        r'see chart below',
        r'see chart above',
        r'see figure below',
        r'see figure above',
        r'see diagram below',
        r'see diagram above',
        r'image shows',
        r'chart shows',
        r'graph shows',
        r'figure shows',
        r'diagram shows',
        r'as shown in the image',
        r'as shown in the chart',
        r'as shown in the figure',
        r'as shown in the diagram',
        r'as you can see in the image',
        r'as you can see in the chart',
        r'click to enlarge',
        r'click to view',
        r'image credit:',
        r'photo credit:',
        r'image courtesy of',
        r'photo courtesy of',
        r'caption:',
        r'figure \d+:',
        r'image \d+:',
        r'chart \d+:',
    ]
    for pattern in visual_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Step 4: Remove author bios and metadata sections
    # Common patterns for author bios
    author_patterns = [
        r'about the author:.*?(?=\n\n|\n[A-Z]|$)',
        r'author bio:.*?(?=\n\n|\n[A-Z]|$)',
        r'written by:.*?(?=\n\n|\n[A-Z]|$)',
        r'by [A-Z][a-z]+ [A-Z][a-z]+.*?(?=\n\n|\n[A-Z]|$)',  # "By John Smith..."
    ]
    for pattern in author_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove common metadata patterns (unless they're part of the main content)
    metadata_patterns = [
        r'published: \d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'published on: \d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'last updated: \d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'updated: \d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'updated on: \d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'posted: \d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'posted on: \d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'tags?: [^\n]+',
        r'categories?: [^\n]+',
        r'category: [^\n]+',
        r'filed under: [^\n]+',
        r'\d+\s+min\s+read',  # "5 min read"
        r'\d+\s+minute\s+read',  # "5 minute read"
        r'reading time:.*',
        r'estimated read time:.*',
        r'by [A-Z][a-z]+ [A-Z][a-z]+',  # Author names at start
        r'author: [A-Z][a-z]+ [A-Z][a-z]+',
        r'written by [A-Z][a-z]+ [A-Z][a-z]+',
    ]
    for pattern in metadata_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Step 5: Remove comment sections
    comment_patterns = [
        r'comments?:.*',
        r'leave a comment.*',
        r'add your comment.*',
        r'join the discussion.*',
        r'comment section.*',
    ]
    for pattern in comment_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Step 6: Remove related articles and non-core sections
    related_patterns = [
        r'related articles?:.*',
        r'you may also like:.*',
        r'read also:.*',
        r'more from [^\n]+:.*',
        r'similar articles?:.*',
        r'recommended reading:.*',
        r'bibliography:.*',
        r'references:.*',
        r'sources:.*',
        r'further reading:.*',
    ]
    for pattern in related_patterns:
        # Remove the header and everything after it until a clear break
        text = re.sub(pattern + '.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove FAQ sections (unless it's the main content - we'll keep if it's substantial)
    # Remove "Conclusion" sections that are just repetitive summaries
    conclusion_patterns = [
        r'^conclusion:.*?(?=\n\n[A-Z]|$)',
        r'^in conclusion:.*?(?=\n\n[A-Z]|$)',
        r'^to conclude:.*?(?=\n\n[A-Z]|$)',
        r'^to sum up:.*?(?=\n\n[A-Z]|$)',
    ]
    for pattern in conclusion_patterns:
        # Only remove if conclusion is short (likely just a recap)
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL))
        for match in reversed(matches):  # Process in reverse to maintain positions
            conclusion_text = match.group(0)
            # If conclusion is less than 200 chars, it's likely just a recap
            if len(conclusion_text) < 200:
                text = text[:match.start()] + text[match.end():]
    
    # Step 7: Remove formatting markers that might have leaked through
    # Remove markdown-style formatting
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)  # Italic
    text = re.sub(r'__([^_]+)__', r'\1', text)  # Bold underscore
    text = re.sub(r'_([^_]+)_', r'\1', text)  # Italic underscore
    text = re.sub(r'~~([^~]+)~~', r'\1', text)  # Strikethrough
    
    # Step 8: Remove social media, engagement, and sharing elements
    social_patterns = [
        r'like us on [^\s]+',
        r'follow us on [^\s]+',
        r'share this [^\s]+',
        r'tweet this',
        r'pin it',
        r'share on facebook',
        r'share on twitter',
        r'share on linkedin',
        r'\d+[kK]?\s+views?',  # "10k views", "100 views"
        r'\d+[kK]?\s+shares?',  # "5k shares"
        r'\d+[kK]?\s+likes?',  # "1k likes"
        r'join \d+[kK]?[,\s]+subscribers?',  # "Join 10,000 subscribers"
        r'join \d+[kK]?[,\s]+readers?',  # "Join 10k readers"
        r'trending now',
        r"editor'?s pick",
        r"editor'?s choice",
        r'most popular',
        r'most read',
        r'viral',
    ]
    for pattern in social_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Step 9: Remove promotional content
    promotional_patterns = [
        r'download our [^\s]+',
        r'download the [^\s]+ guide',
        r'get your free [^\s]+',
        r'try it free',
        r'try for free',
        r'get started today',
        r'get started now',
        r'start your free trial',
        r'sign up for [^\s]+ newsletter',
        r'subscribe to [^\s]+ newsletter',
        r'join our newsletter',
        r'newsletter signup',
        r'newsletter sign-up',
        r'enter your email',
        r'get exclusive access',
        r'limited time offer',
        r'special offer',
        r'buy now',
        r'purchase now',
        r'order now',
        r'learn more about [^\s]+ product',
        r'check out [^\s]+ service',
    ]
    for pattern in promotional_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Step 10: Remove cookie/privacy notices that might appear in text
    cookie_patterns = [
        r'we use cookies.*',
        r'cookie policy.*',
        r'privacy policy.*',
        r'accept cookies.*',
        r'cookie settings.*',
    ]
    for pattern in cookie_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Step 11: Remove recap/repetitive sentences
    recap_patterns = [
        r'as we mentioned earlier[^\n]*',
        r'as mentioned above[^\n]*',
        r'as stated previously[^\n]*',
        r'as discussed earlier[^\n]*',
        r'to recap[^\n]*',
        r'to summarize[^\n]*',
        r'in summary[^\n]*',
        r'remember that[^\n]*',
        r'keep in mind that[^\n]*',
    ]
    for pattern in recap_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Step 12: Remove very short lines (enhanced)
    # Remove multiple consecutive newlines (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove multiple consecutive spaces
    text = re.sub(r' {2,}', ' ', text)
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    # Remove empty lines at the start and end
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    text = '\n'.join(lines)
    
    # Step 12: Remove very short lines (enhanced)
    # These are typically short, repetitive phrases or artifacts
    ui_phrases = [
        'home',
        'about',
        'contact',
        'privacy',
        'terms',
        'cookie',
        'subscribe',
        'newsletter',
        'search',
        'menu',
        'close',
        'open',
        'next',
        'previous',
        'back',
        'top',
    ]
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line_stripped = line.strip()
        # Remove lines under 10 characters (usually artifacts)
        if len(line_stripped) < 10:
            # But keep if it's a valid heading (all caps short headings)
            if not (line_stripped.isupper() and len(line_stripped) >= 3):
                continue
        # Skip lines that are just UI phrases
        if line_stripped.lower() in ui_phrases and len(line_stripped) < 20:
            continue
        # Skip lines that are just punctuation or symbols
        if re.match(r'^[^\w\s]+$', line_stripped):
            continue
        # Skip single-word lines (unless they're headings)
        words = line_stripped.split()
        if len(words) == 1 and len(line_stripped) < 15 and not line_stripped.isupper():
            continue
        cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)
    
    # Step 13: Condense repetitive content
    text = _condense_repetitive_content(text)
    
    # Step 14: Remove non-essential background/context
    text = _remove_non_essential_context(text)
    
    # Step 15: Final cleanup - remove any remaining artifacts
    # Remove standalone brackets or parentheses that might be leftover
    text = re.sub(r'^\s*[\[\]()]\s*$', '', text, flags=re.MULTILINE)
    # Remove lines that are just numbers or symbols
    text = re.sub(r'^\s*[\d\W]+\s*$', '', text, flags=re.MULTILINE)
    
    # Step 16: Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    # Step 17: Smart truncation if still too long (after all other cleaning)
    text = _smart_truncate(text, max_length=max_length)
    
    # Final whitespace normalization
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text


def _condense_repetitive_content(text: str) -> str:
    """
    Condense repetitive content:
    - If the same point is made multiple times, keep it once
    - If there's a long list of examples, cut it down to the best 3-5
    - Summarize very long quotes into key points
    """
    lines = text.split('\n')
    if len(lines) < 3:
        return text
    
    # Detect and remove near-duplicate sentences
    cleaned_lines = []
    seen_sentences = set()
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            cleaned_lines.append(line)
            continue
        
        # Create a normalized version for comparison (lowercase, no punctuation)
        normalized = re.sub(r'[^\w\s]', '', line_stripped.lower())
        # Skip if we've seen a very similar sentence recently
        if normalized in seen_sentences:
            continue
        
        # Add to seen set (keep last 50 sentences to avoid false positives)
        seen_sentences.add(normalized)
        if len(seen_sentences) > 50:
            # Remove oldest entries (simple FIFO)
            seen_sentences = set(list(seen_sentences)[-50:])
        
        cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Condense long lists (numbered or bulleted)
    # Look for patterns like "1. ... 2. ... 3. ..." with many items
    list_pattern = r'(\d+\.\s+[^\n]+(?:\n\d+\.\s+[^\n]+){10,})'  # 11+ items
    matches = list(re.finditer(list_pattern, text, re.MULTILINE))
    
    for match in reversed(matches):
        list_text = match.group(0)
        items = re.findall(r'\d+\.\s+([^\n]+)', list_text)
        if len(items) > 5:
            # Keep first 2-3 and last 2-3 items
            keep_count = min(3, len(items) // 3)
            condensed = items[:keep_count] + ['...'] + items[-keep_count:]
            # Reconstruct the list
            new_list = '\n'.join([f'{i+1}. {item}' for i, item in enumerate(condensed)])
            text = text[:match.start()] + new_list + text[match.end():]
    
    # Condense very long quotes (over 300 chars) - keep first and last parts
    quote_pattern = r'["""]([^"""]{300,})["""]'
    matches = list(re.finditer(quote_pattern, text))
    
    for match in reversed(matches):
        quote_text = match.group(1)
        if len(quote_text) > 300:
            # Keep first 150 and last 100 chars
            condensed_quote = quote_text[:150] + '...' + quote_text[-100:]
            text = text[:match.start(1)] + condensed_quote + text[match.end(1):]
    
    return text


def _remove_non_essential_context(text: str) -> str:
    """
    Remove non-essential background/context:
    - Overly detailed historical background
    - Tangential anecdotes
    - "As we mentioned earlier..." recap sentences (already handled, but catch more)
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    # Patterns that indicate tangential or overly detailed background
    tangential_patterns = [
        r'^in \d{4},',  # "In 1923," - likely historical tangent
        r'^back in \d{4},',
        r'^historically,',
        r'^in ancient times,',
        r'^centuries ago,',
        r'^decades ago,',
    ]
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            cleaned_lines.append(line)
            continue
        
        # Skip lines that match tangential patterns (unless they're short and likely important)
        is_tangential = False
        for pattern in tangential_patterns:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                # Only remove if the line is long (likely detailed background)
                if len(line_stripped) > 100:
                    is_tangential = True
                    break
        
        if not is_tangential:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def _smart_truncate(text: str, max_length: int = 50000) -> str:
    """
    Smart truncation if text is still too long after cleaning.
    Strategy:
    - Keep first 30-40% (intro and main points)
    - Keep middle 40% (core content)
    - Cut last 20-30% (usually recap and CTAs)
    
    Args:
        text: Text to potentially truncate
        max_length: Maximum desired length (default 50k chars)
        
    Returns:
        Truncated text if needed, otherwise original
    """
    if len(text) <= max_length:
        return text
    
    # Calculate sections
    total_length = len(text)
    first_section_end = int(total_length * 0.35)  # First 35%
    middle_section_start = int(total_length * 0.30)  # Start of middle
    middle_section_end = int(total_length * 0.70)  # End of middle (70% total)
    
    # Find good break points (paragraph breaks)
    def find_paragraph_break(text: str, target_pos: int) -> int:
        """Find the nearest paragraph break near target position"""
        # Look for double newlines within 500 chars
        search_start = max(0, target_pos - 500)
        search_end = min(len(text), target_pos + 500)
        search_text = text[search_start:search_end]
        
        # Find all paragraph breaks
        breaks = [m.start() + search_start for m in re.finditer(r'\n\n+', search_text)]
        if breaks:
            # Return the break closest to target
            return min(breaks, key=lambda x: abs(x - target_pos))
        return target_pos
    
    first_break = find_paragraph_break(text, first_section_end)
    middle_start_break = find_paragraph_break(text, middle_section_start)
    middle_end_break = find_paragraph_break(text, middle_section_end)
    
    # Combine: first section + middle section
    truncated = text[:first_break] + '\n\n' + text[middle_start_break:middle_end_break]
    
    # If still too long, be more aggressive
    if len(truncated) > max_length:
        # Just take first 60% and find a good break point
        target = int(len(text) * 0.60)
        break_point = find_paragraph_break(text, target)
        truncated = text[:break_point]
    
    return truncated
