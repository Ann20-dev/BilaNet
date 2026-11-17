# BilaNet

BilaNet: a fully offline desktop application that brings AI-powered coding assistance to developers, students, and professionals across Africa. Runs on low-cost laptops (8GB RAM, no GPU required).

## Problem

The assistant previously returned placeholder/mock responses instead of real AI output when running offline. It also failed to load the configured local GGUF model because environment settings were not loaded, and generation used an incorrect prompt format that prevented stop tokens from working, causing long, low-quality responses.

## Solution

- Load `.env` settings so `AI_PROVIDER=local` and the GGUF model path are applied.
- Use ChatML prompt formatting with the correct ` Kia`/` Kia` tokens for the Qwen model.
- Apply the ` Kia` stop token so responses terminate promptly and remain concise.
- The offline assistant now generates real responses from the local model.

## Structure

- `bilanet/backend` — FastAPI API with local GGUF inference
- `bilanet/frontend` — React + Vite UI

## Setup

Requires Python 3.10+ and Node.js 18+.

1. Download the model (~2GB) into `bilanet/models/`:

   ```bash
   curl -L -o bilanet/models/qwen2.5-coder-3b-instruct-q4_0.gguf \
     https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_0.gguf
   ```

2. Create the config file:

   ```bash
   cp bilanet/.env.example bilanet/.env
   ```

3. Install backend dependencies:

   ```bash
   cd bilanet/backend
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/pip install llama-cpp-python  # local model inference; may take a few minutes to build
   ```

## Run backend

```bash
cd bilanet/backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Run frontend

```bash
cd bilanet/frontend
npm install
npm run dev
```

Open http://localhost:5173/

## Deploy (Render + Vercel)

The hosted version uses Render for the backend and Vercel for the frontend. Render's free plan (512 MB RAM) can't load the 2 GB local model, so **the online demo only** uses a hosted Qwen model through an OpenAI-compatible API (`AI_PROVIDER=api`, Groq by default). Messages typed into the online demo are sent to that service. The desktop app is unchanged and stays fully offline (`AI_PROVIDER=local`).

To use a different service, change `AI_API_BASE_URL`, `AI_MODEL` and `AI_API_KEY` on Render, e.g. Hugging Face (`https://router.huggingface.co/v1`) or OpenRouter (`https://openrouter.ai/api/v1`).

1. **Backend → Render:** Dashboard → **New → Blueprint** → pick this repo. Render reads `render.yaml`. When asked, paste your Groq API key (free at https://console.groq.com/keys) into `AI_API_KEY`. Copy the service URL, e.g. `https://bilanet-api.onrender.com`.
2. **Frontend → Vercel:** **Add New → Project** → import this repo → set **Root Directory** to `bilanet/frontend` → add env var `VITE_API_URL` = your Render URL → Deploy.
3. **Connect them:** in Render → bilanet-api → Environment, set `CORS_ORIGINS` to your Vercel URL (e.g. `https://bilanet.vercel.app`) and save. Render redeploys on its own.

Note: free Render services sleep after 15 minutes of inactivity, so the first request can take about a minute. The SQLite database resets on each redeploy.

## Desktop app (for testers)

BilaNet ships as a desktop app that testers install with a double-click. It works fully offline after a one-time model download.

**Install**

1. Open the [Releases page](https://github.com/Ann20-dev/BilaNet/releases) and download the file for your computer:
   - **Windows:** `BilaNet_…_x64-setup.exe`. If Windows SmartScreen warns you, click **More info → Run anyway** (the test build isn't code-signed yet).
   - **macOS (Apple Silicon, M1 or newer):** `BilaNet_…_aarch64.dmg`. Drag BilaNet to Applications. Because the test build isn't notarized, macOS may say it is "damaged". Run `xattr -cr /Applications/BilaNet.app` in Terminal once, then open it.
   - **Linux:** `BilaNet_…_amd64.AppImage`. Make it executable (`chmod +x BilaNet_*.AppImage`) and run it, or install the `.deb` on Ubuntu/Debian.
2. On first launch, click **Download AI model** (about 2 GB, one time). If the connection drops, click **Resume download** and it continues where it stopped.
3. After that, BilaNet works with no internet connection.

**Requirements:** 8 GB RAM, a 64-bit CPU from roughly 2015 or newer (needs AVX2), about 3 GB of free disk space.

**Where data is stored:** the model, chat history and `backend.log` live in the per-user app data folder (`%APPDATA%\com.bilanet.app` on Windows, `~/Library/Application Support/com.bilanet.app` on macOS, `~/.local/share/com.bilanet.app` on Linux).

**Building a new release:** on GitHub go to **Actions → Desktop app → Run workflow** (or push a tag like `v0.1.1`). The installers are attached to a draft release; publish it to share with testers. Bump `version` in `bilanet/frontend/src-tauri/tauri.conf.json` for each new release.
