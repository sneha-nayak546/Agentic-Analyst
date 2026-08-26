# Cloud GPU Setup for Remote LLM

This guide provides instructions on how to set up Ollama on a free cloud GPU environment (like Kaggle or Google Colab) and expose it securely so your local Agentic-Analyst app can use it.

## 1. Setup on Kaggle (Temporary Development/Testing)

Kaggle provides free GPU access which is perfect for running `qwen2.5-coder:7b`. However, **Kaggle kernels are ephemeral** and will shut down after your session ends or maxes out the timeout (usually 12 hours). This is for development/testing, NOT a permanent production server.

### Steps in Kaggle:
1. Create a new Notebook in Kaggle.
2. In the right sidebar, expand **Accelerator** and select **GPU P100** or **GPU T4x2**.
3. Turn ON the **Internet** toggle in the sidebar.
4. Add the following code blocks to your notebook and run them:

**Cell 1: Install & Start Ollama**
```bash
# Install Ollama
!curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama in the background
import subprocess
import time

subprocess.Popen(["ollama", "serve"])
time.sleep(5)  # Wait for it to start
```

**Cell 2: Pull the Model**
```bash
# Pull the required model
!ollama run qwen2.5-coder:7b
```

**Cell 3: Expose via LocalTunnel**
```bash
# Install localtunnel
!npm install -g localtunnel

# Start localtunnel on port 11434
!lt --port 11434 --subdomain my-unique-agent-llm
```
*Note: Note the URL output by localtunnel (e.g., `https://my-unique-agent-llm.loca.lt`).*

## 2. Setup on Local Machine

Now that your remote LLM is running, point your local Agentic-Analyst app to it.

1. Open PowerShell on your local machine.
2. Set the environment variable to your localtunnel URL.
   ```powershell
   $env:OLLAMA_BASE_URL="https://my-unique-agent-llm.loca.lt"
   ```
3. Start the application:
   ```powershell
   python start_server.py
   ```

*Note: The localtunnel warning page (HTTP 403 / 500 issue) is now handled automatically by the application via the `Bypass-Tunnel-Reminder` header.*

## 3. Persistent Production Deployment (Alternative)

If you need a 24/7 endpoint, you cannot use Kaggle. You must use a paid service like:
- **RunPod**
- **AWS EC2 (g4dn instances)**
- **Vultr Cloud GPU**

For production, you should expose the Ollama port (11434) securely using Nginx with HTTPS and basic authentication, or via a VPN (Tailscale, ZeroTier), rather than relying on ephemeral tunnels like LocalTunnel or ngrok.
