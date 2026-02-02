import ollama

def warmup_llm():
    try:
        ollama.generate(
            model="phi3:mini",
            prompt="Hello",
            options={
                "num_predict": 1,
                "temperature": 0
            }
        )
        print("LLM warmed up")
    except Exception as e:
        print("LLM warmup failed:", e)
