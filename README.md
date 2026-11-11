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
