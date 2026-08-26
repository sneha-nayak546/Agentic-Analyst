# Agentic-Analyst

## Local vs Remote LLM Configuration

This project relies on Ollama and the `qwen2.5-coder:7b` model to translate natural language into SQL.
By default, the application expects Ollama to be running locally on your machine.

### Local Ollama Setup (Default)
1. Install [Ollama](https://ollama.ai/).
2. Pull the model:
   ```bash
   ollama run qwen2.5-coder:7b
   ```
3. Start the application. The system defaults to `http://localhost:11434`.

### Remote Ollama Setup (Cloud GPU)
If your local machine (e.g., Intel Graphics) is too slow for LLM inference, you can run Ollama on a free cloud GPU (like Kaggle, Colab, or RunPod) and connect your local application to it.

1. Set up your Cloud GPU following the instructions in [cloud_gpu_setup.md](cloud_gpu_setup.md).
2. Once you have your secure remote URL (e.g., from Ngrok or LocalTunnel), set the `OLLAMA_BASE_URL` environment variable locally before starting the server.

**PowerShell:**
```powershell
$env:OLLAMA_BASE_URL="https://your-ngrok-url.ngrok.io"
python start_server.py
```

**Bash/Zsh:**
```bash
export OLLAMA_BASE_URL="https://your-ngrok-url.ngrok.io"
python start_server.py
```

### How to test the connection
Once the server is running, you can test if the FastAPI application can reach your configured Ollama endpoint by visiting:
```
http://localhost:8000/api/llm/health
```

You should see a JSON response indicating whether it is online, along with the configured URL and model name.

### How to switch between local and remote inference
To switch back to local inference, simply unset the environment variable or set it back to localhost:
```powershell
$env:OLLAMA_BASE_URL="http://localhost:11434"
```
