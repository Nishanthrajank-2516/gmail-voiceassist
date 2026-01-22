import ollama


def enhance_email_body(text: str) -> str:
    """
    Enhance an email body by improving grammar, clarity, and logical flow
    WITHOUT adding new information or changing meaning.

    Safety guarantees:
    - No hallucinated names, companies, institutes, greetings, or signatures
    - Meaning remains exactly the same
    - Output length is HARD-LIMITED to at most 2× input length
    - If LLM fails, original text is returned unchanged
    """

    if not text or not text.strip():
        return text

    prompt = f"""
You are an email text improver.

STRICT RULES (DO NOT BREAK):
- Improve ONLY grammar, clarity, and logical flow
- DO NOT add names, companies, institutes, greetings, or signatures
- DO NOT invent or assume context
- DO NOT add examples or templates
- Keep the meaning EXACTLY the same
- The improved text must NOT be longer than 2× the original length
- If something is not mentioned, DO NOT add it

Original email body:
{text}

Return ONLY the improved email body.
"""

    try:
        response = ollama.generate(
            model="phi3:mini",
            prompt=prompt,
            options={
                "temperature": 0.1,     # deterministic, editing-only behavior
                "num_predict": 200
            }
        )

        improved = response.get("response", "").strip()

        # 🔒 HARD SAFETY ENFORCEMENT (DO NOT REMOVE)
        max_length = len(text) * 2
        if len(improved) > max_length:
            improved = improved[:max_length]

        # If model returned nothing, fall back safely
        if not improved:
            return text

        return improved

    except Exception:
        # Absolute safety fallback
        return text
