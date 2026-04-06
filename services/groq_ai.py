"""
Atlas Pharma QMS — Groq AI Service
Uses Groq API for ultra-fast, rate-limit friendly review triage and sentiment analysis.
"""

import os
from groq import Groq

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_MODEL_NAME = "llama-3.3-70b-versatile"

def _get_client():
    """Configure and return a Groq client instance."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY environment variable is not set. "
            "Please set it before running the app."
        )
    return Groq(api_key=api_key)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def categorize_review(review_text: str) -> str:
    """
    Use Groq to classify a product complaint into one of:
      - Critical  (safety / regulatory risk)
      - Major     (significant quality deviation)
      - Minor     (cosmetic or low-impact observation)

    Returns the category string. Falls back to keyword heuristics on error.
    """
    prompt = f"""You are a pharmaceutical quality assurance AI.
Classify the following product complaint into exactly ONE of these categories:
- Critical (poses a safety or regulatory risk to patients)
- Major (significant quality deviation that affects product efficacy or appearance)
- Minor (cosmetic issue or low-impact observation with no safety concern)

Return ONLY the single word: Critical, Major, or Minor. Reply with nothing else.

Complaint:
\"\"\"{review_text}\"\"\"
"""
    try:
        client = _get_client()
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=_MODEL_NAME,
            temperature=0.0
        )
        result = chat_completion.choices[0].message.content.strip()

        # Validate response
        for cat in ("Critical", "Major", "Minor"):
            if cat.lower() in result.lower():
                return cat
        return "Major"  # fallback
    except Exception as e:
        print(f"[Groq AI] Categorization error: {e}")
        # Fallback heuristic when API fails
        text_lower = review_text.lower()
        if any(word in text_lower for word in ['broken', 'crumbled', 'safety', 'sick', 'mold', 'glass', 'contamination']):
            return "Critical"
        if any(word in text_lower for word in ['taste', 'thinner', 'color', 'smell', 'delivery', 'late', 'box']):
            return "Minor"
        return "Major"


def analyze_sentiment(review_text: str) -> str:
    """
    Use Groq to analyse the sentiment of a review.
    Returns one of: Positive, Negative, Neutral.
    Falls back to heuristics on error.
    """
    prompt = f"""You are a pharmaceutical quality assurance AI.
Analyze the sentiment of the following product feedback.
Return ONLY one word: Positive, Negative, or Neutral. Reply with nothing else.

Feedback:
\"\"\"{review_text}\"\"\"
"""
    try:
        client = _get_client()
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=_MODEL_NAME,
            temperature=0.0
        )
        result = chat_completion.choices[0].message.content.strip()

        for sent in ("Positive", "Negative", "Neutral"):
            if sent.lower() in result.lower():
                return sent
        return "Neutral"
    except Exception as e:
        print(f"[Groq AI] Sentiment error: {e}")
        # Fallback heuristic when API fails
        text_lower = review_text.lower()
        if any(word in text_lower for word in ['good', 'great', 'excellent', 'happy', 'love', 'perfect']):
            return "Positive"
        if any(word in text_lower for word in ['bad', 'terrible', 'awful', 'sick', 'broken', 'disappointed', 'unusual', 'different']):
            return "Negative"
        return "Neutral"


def categorize_and_analyze(review_text: str) -> tuple[str, str]:
    """
    Convenience: run both categorization and sentiment in one call.
    Returns (category, sentiment).
    """
    category = categorize_review(review_text)
    sentiment = analyze_sentiment(review_text)
    return category, sentiment
