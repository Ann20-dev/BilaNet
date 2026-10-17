# BilaNet

Africa Code Assistant: a fully offline desktop application that brings AI-powered coding assistance to developers, students, and professionals across Africa. Runs on low-cost laptops (8GB RAM, no GPU required).

## Problem

The assistant previously returned placeholder/mock responses instead of real AI output when running offline. It also failed to load the configured local GGUF model because environment settings were not loaded, and generation used an incorrect prompt format that prevented stop tokens from working, causing long, low-quality responses.

## Solution

- Load `.env` settings so `AI_PROVIDER=local` and the GGUF model path are applied.
- Use ChatML prompt formatting with the correct ` Kia`/` Kia` tokens for the Qwen model.
- Apply the ` Kia` stop token so responses terminate promptly and remain concise.
- The offline assistant now generates real responses from the local model.

## Structure

- `africa-code-assistant/backend` — FastAPI API with local GGUF inference
- `africa-code-assistant/frontend` — React + Vite UI

## Run backend

```bash
cd africa-code-assistant/backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Run frontend

```bash
cd africa-code-assistant/frontend
npm install
npm run dev
```

Open http://localhost:5173/
EOF