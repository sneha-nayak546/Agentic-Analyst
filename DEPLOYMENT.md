# Production & Demo Deployment Guide: JGH AI Analytics Platform

This guide details the complete deployment process to host the JGH AI Analytics application so that your Team Lead can test it via a public HTTPS URL without installing Ollama, Python, Qwen, model files, or any model runtimes on their machine.

---

## 1. Architecture

```
Team Lead (Browser)
       ↓ (Public HTTPS URL via Cloudflare Tunnel / Cloud Server)
 Cloudflare Edge / Reverse Proxy
       ↓ (Port 8000)
  FastAPI Backend Server (app/api/main.py)
       ├── Serves Built React SPA Frontend (app/static)
       ├── Intent Router & Vector RAG Retriever (app/agent, app/chroma)
       ├── Model Service Engine (app/llm/sql_generator.py)
       │     ├── 1. Sub-2ms Deterministic Enterprise Synthesizer
       │     └── 2. Ollama Qwen2.5-Coder 7B (127.0.0.1:11434)
       └── Database Read Engine (app/database/config.py & read_executor.py)
             └── MySQL Database (jghMasterDB via TLS/SSL + AES-256 decrypted RAM creds)
```

---

## 2. Hosting Platform Selected

**Recommended Strategy**: **Host Workstation / Cloud Virtual Machine + Cloudflare Tunnel (`cloudflared`)**  
**Alternative Strategy**: **Render / Koyeb / Docker Container Host with Remote DB + LLM API Fallback**

---

## 3. Why It Was Selected

- **Zero Software Installation for Team Lead**: The Team Lead opens a standard public HTTPS web link (`https://xxxx.trycloudflare.com`) in any modern web browser.
- **Bypasses Free Tier RAM Limits**: Free cloud container platforms (such as Render Free Tier) limit containers to **512 MB RAM**. Running Qwen2.5-Coder 7B requires **~4.7 GB RAM**; attempting to run Ollama on Render free tier results in instant Out-Of-Memory (OOM) crashes.
- **100% Free with No Expiration or Credit Card**: Cloudflare Tunnels provide free, unlimited, secure HTTPS exposure for HTTP servers.
- **Privacy & Security**: Ollama (`127.0.0.1:11434`) and MySQL are restricted to internal localhost interfaces and are never exposed directly to the public internet.

---

## 4. Prerequisites

1. **Server / Host Machine**: Windows/Linux/macOS with at least 8 GB RAM (16 GB recommended for GPU acceleration).
2. **Python Environment**: Python 3.10+ with `requirements.txt` installed.
3. **Ollama**: Installed locally on the server with model loaded: `ollama pull qwen2.5-coder:7b`.
4. **MySQL Database**: MySQL 8.0 server with `jghMasterDB` dataset.
5. **Cloudflare Tunnel (`cloudflared`)**: Downloadable executable from Cloudflare.

---

## 5. Environment Variables

Configuration is loaded from environment variables or `.env`:

| Variable Name | Default Value | Description |
|---|---|---|
| `DB_HOST` | `localhost` | MySQL Server Host IP / Domain |
| `DB_PORT` | `3306` | MySQL Server Port |
| `DB_NAME` | `jghMasterDB` | Database Name |
| `DB_USER` | `root` | Database Username |
| `DB_PASSWORD` | `""` | Database Password |
| `ENCRYPTED_DB_CONFIG` | *(Optional)* | AES-256 Fernet encrypted credential payload |
| `MASTER_SECRET_KEY` | *(Optional)* | Key for decrypting `ENCRYPTED_DB_CONFIG` (or stored in `.master.key`) |
| `ENABLE_LLM_FALLBACK` | `0` | Set `1` to enable Ollama Qwen2.5-Coder calls; `0` for instant deterministic synthesizer |
| `LLM_MODEL` | `qwen2.5-coder:7b` | Ollama model identifier |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama API service endpoint |
| `PORT` | `8000` | FastAPI server port |

---

## 6. How to Deploy

### Option A: Direct Python Server Deployment (Fastest)

1. Open PowerShell / Terminal in project directory:
   ```powershell
   cd c:\Users\nayak_o7hopi6\Desktop\Agent
   ```
2. Activate virtual environment and verify diagnostics:
   ```powershell
   .\venv\Scripts\python.exe start_server.py
   ```
3. In a second terminal, launch Cloudflare Tunnel to generate a public HTTPS URL:
   ```powershell
   cloudflared tunnel --url http://localhost:8000
   ```
4. Copy the generated HTTPS link (e.g. `https://xxxx.trycloudflare.com`) and send it to your Team Lead.

### Option B: Docker Container Deployment

1. Build the Docker container:
   ```bash
   docker build -t jgh-ai-analytics .
   ```
2. Run container using docker-compose:
   ```bash
   docker-compose up -d
   ```
3. Expose port 8000 over Cloudflare Tunnel:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

---

## 7. How to Start the Model

Ensure Ollama is running on the host machine:
```powershell
# Start Ollama service
ollama serve

# Verify Qwen model is downloaded
ollama run qwen2.5-coder:7b "SELECT 1;"
```

---

## 8. How FastAPI Connects to the Model

- In `app/llm/sql_generator.py`, FastAPI connects to Ollama via HTTP REST calls on `OLLAMA_HOST` (`http://127.0.0.1:11434`).
- It checks health via `is_ollama_online()` hitting `/api/tags`.
- If Ollama is offline or `ENABLE_LLM_FALLBACK=0`, FastAPI seamlessly falls back to the built-in sub-2ms deterministic enterprise SQL synthesizer `_synthesize_sql_from_prompt()`.

---

## 9. How the Frontend Connects to FastAPI

- The React SPA frontend (`frontend/src/`) compiles static assets into `app/static/`.
- All component API calls use relative paths (`/query`, `/schema`, `/history`, `/admin`, `/reports`, `/export`).
- FastAPI mounts `app/static` and serves the UI directly at `GET /`. When the Team Lead loads `https://xxxx.trycloudflare.com/`, the browser calls relative endpoints on the same origin.

---

## 10. Database Configuration

- Connection parameters are retrieved in `app/database/config.py`.
- Supports encrypted payloads (`ENCRYPTED_DB_CONFIG`) decrypted via `MASTER_SECRET_KEY` in RAM.
- Falls back to `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.
- Connections use SQLAlchemy connection pooling with `mysql+pymysql` and SSL/TLS wire encryption.

---

## 11. How to Test the Deployed Application

1. Open the public HTTPS URL in Google Chrome / Edge / Firefox on any computer or mobile device.
2. Click **Collaborator Chat** and ask:
   - *"Show top 10 retailers by total earnings in July 2026"*
   - *"What is the total wallet balance across all users?"*
3. Verify that the SQL query is generated, executed, rendered in the Data Grid, and downloadable via CSV/Excel/PDF export buttons.
4. Check **Schema Admin** (`/admin`) and **History & Audit** (`/history`) to confirm real-time query logging.

---

## 12. How Multiple Users Are Handled

- **Stateless Session Isolation**: Each HTTP request to `/query` is atomic. No global conversation memory or cross-user state mutation occurs.
- **Incognito & Audit Support**: Headers (`X-Incognito-Mode`) and parameters control audit logging per request context.
- **Model Request Queuing**: Concurrent user queries hitting the model are safely queued by Uvicorn and Ollama worker queues.

---

## 13. Known Free-Tier Limitations

- **512 MB Cloud RAM Restriction**: Cloud container free tiers (Render/Koyeb) cannot host Ollama 7B locally. Using Cloudflare Tunnel on host hardware avoids this restriction completely.
- **Host Availability**: When using Cloudflare Tunnel on your host machine, the host computer must remain powered on and connected to the internet during team lead testing.

---

## 14. How to Update the Application

1. Make code changes in backend (`app/`) or frontend (`frontend/src/`).
2. If frontend changes were made, rebuild static assets:
   ```powershell
   cd frontend
   npm run build
   ```
3. Restart FastAPI server:
   ```powershell
   python start_server.py
   ```

---

## 15. How to Update the Model

1. Pull updated Ollama model weights:
   ```powershell
   ollama pull qwen2.5-coder:7b
   ```
2. To switch to a different model, set environment variable `LLM_MODEL=qwen2.5-coder:14b` in `.env` and restart server.

---

## 16. How to Rollback

- **Code Rollback**: Revert Git commits (`git checkout HEAD~1`) and rebuild frontend (`npm run build`).
- **Configuration Rollback**: Restore previous `.env` settings or master key `.master.key`.

---

## 17. How to Stop / Delete the Deployment

1. **Stop Cloudflare Tunnel**: Press `Ctrl + C` in the `cloudflared` terminal window.
2. **Stop FastAPI Server**: Press `Ctrl + C` in the server terminal or run `docker-compose down`.
3. The public HTTPS URL terminates immediately upon stopping `cloudflared`.
