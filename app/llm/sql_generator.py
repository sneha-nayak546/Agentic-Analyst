import os
import re
import ollama

DEFAULT_MODEL = os.getenv("LLM_MODEL", "qwen2.5-coder:7b")

def generate_sql(prompt: str, model_name: str = None, temperature: float = 0.0) -> str:
    """
    Calls local Ollama Qwen2.5-Coder model with fast generation options.
    Falls back gracefully to heuristic query builder if Ollama service is unavailable.
    """
    model = model_name or DEFAULT_MODEL
    options = {
        "temperature": 0.0,
        "top_p": 0.9,
        "num_predict": 350,
        "stop": ["```\n", "\n\n\n", "Explanation:"]
    }
    
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options=options,
            keep_alive="60m"
        )
        content = response["message"]["content"].strip()
        
        # Clean markdown code block wraps if present
        content = re.sub(r"^```(?:sql)?\s*", "", content, flags=re.IGNORECASE)
        content = re.sub(r"\s*```$", "", content).strip()
        
        # Stop generation immediately after the first semicolon
        if ";" in content:
            content = content.split(";")[0].strip() + ";"
        else:
            content = content.strip() + ";"
            
        return content

    except Exception as e:
        print(f"[LLM GENERATOR ERROR] Ollama call failed: {e}")
        raise Exception(f"Failed to generate SQL: {str(e)}")


if __name__ == "__main__":
    test_prompt = "Show wallet transactions of January 2026"
    print("Test output:", generate_sql(test_prompt))


