import os
import re
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

# Replace with the actual endpoint ID once deployed
VERTEX_ENDPOINT_ID = os.getenv("VERTEX_ENDPOINT_ID", "1234567890123456789")
PROJECT_ID = "agent-jgh"
LOCATION = "us-central1"

def generate_sql_vertex(prompt: str, temperature: float = 0.0) -> str:
    """
    Generate SQL using the Vertex AI Custom Endpoint hosting Qwen.
    """
    try:
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        
        endpoint = aiplatform.Endpoint(
            endpoint_name=f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{VERTEX_ENDPOINT_ID}"
        )
        
        # vLLM container typically expects an openai-like chat completion payload
        # depending on the exact serving container format. Assuming generic Vertex vLLM schema here.
        instance = {
            "prompt": f"<|im_start|>system\nYou are an expert MySQL Data Analyst. Write only valid MySQL SELECT queries. Output the SQL query inside ```sql code blocks.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n",
            "temperature": temperature,
            "max_tokens": 300,
            "top_p": 0.9,
            "stop": ["Explanation:"]
        }
        
        # This is a dry run safety check
        if VERTEX_ENDPOINT_ID == "1234567890123456789":
            print("[VERTEX WARNING] Using placeholder endpoint ID. Returning dummy SQL.")
            return "SELECT 'Dummy Vertex AI Result' AS result;"
            
        instances = [instance]
        response = endpoint.predict(instances=instances)
        
        # Parse output from vLLM Vertex response
        if response.predictions:
            content = response.predictions[0]
            # Standard cleanup for markdown blocks
            content = re.sub(r"^```(?:sql)?\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"\s*```$", "", content).strip()
            if content and ";" in content:
                return content.split(";")[0].strip() + ";"
            if content:
                return content
                
        return ""
        
    except Exception as e:
        print(f"[VERTEX ERROR] Failed to query Vertex AI endpoint: {e}")
        return ""
