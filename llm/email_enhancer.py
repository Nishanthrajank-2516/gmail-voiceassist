import ollama

def enhance_email_body(text: str) -> str:
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
        res = ollama.generate(
            model="phi3:mini",
            prompt=prompt,
            options={
                "temperature": 0.1,
                "num_predict": 200
            }
        )
        return res["response"].strip()
    except Exception:
        return text
