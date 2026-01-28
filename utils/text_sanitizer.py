import re
import bleach

def scrub_text(text):
    """
    Industrial-grade text sanitizer to remove AI artifacts and enforce
    professional typography.
    """
    if not text:
        return ""

    # 1. Clean HTML first using Bleach (Security)
    # Allow strict subset of tags for blog posts
    allowed_tags = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'h2', 'h3', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote']
    allowed_attrs = {'a': ['href', 'title', 'target']}
    clean_text = bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)

    # 2. Remove AI-isms and common artifacts
    
    # Remove "As an AI language model..." variants
    clean_text = re.sub(r"(?i)as an ai language model.*?,", "", clean_text)
    
    # Remove multiple dashes/underscores used as dividers (AI common habit)
    # e.g. "___" or "---"
    clean_text = re.sub(r'(\s*[-_]{3,}\s*)', '\n<hr>\n', clean_text)

    # Remove the "Key Takeaways:" style headers if they look robotic
    # (Optional, purely stylistic)

    # 3. Typographic Fixes
    # Fix spacing around punctuation commonly messed up by bad parsers
    clean_text = re.sub(r'\s+([,.;:?!])', r'\1', clean_text)
    
    # Smart quotes (simple replacement)
    clean_text = clean_text.replace('"', '"').replace('"', '"')
    
    return clean_text.strip()

def detect_ai_content(text):
    """
    Returns a score (0-100) of how likely the text is AI-generated based on
    keyword density of common GPT phrases.
    """
    ai_phrases = [
        "delve into", "in conclusion", "it is important to note",
        "comprehensive guide", "landscape of", "realm of",
        "testament to", "tapestry of", "fostering a sense of"
    ]
    
    score = 0
    text_lower = text.lower()
    
    found_phrases = []
    for phrase in ai_phrases:
        if phrase in text_lower:
            score += 10
            found_phrases.append(phrase)
            
    return min(score, 100), found_phrases
