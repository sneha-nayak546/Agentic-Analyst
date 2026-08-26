import ollama
client = ollama.Client(host='http://localhost:11434')
response = client.chat(
    model='qwen2.5-coder:7b',
    messages=[
        {"role": "system", "content": "You are an expert MySQL Data Analyst. Write only valid MySQL SELECT queries. Output the SQL query inside ```sql code blocks."},
        {"role": "user", "content": "Generate a table of retailers linked to distributor 5997"}
    ],
    options={"temperature": 0.0, "top_p": 0.9, "num_predict": 300, "stop": ["```", "Explanation:"]}
)
print("RESPONSE:", response.message.content)
