# BilaNet

Africa Code Assistant: a fully offline desktop application that brings AI-powered coding assistance to developers, students, and professionals across Africa. Runs on low-cost laptops (8GB RAM, no GPU required).

## Structure

- `africa-code-assistant/backend` — FastAPI API with local GGUF inference
- `africa-code-assistant/frontend` — React + Vite UI

## Run backend

```bash
cd africa-code-assistant/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Run frontend

```bash
cd africa-code-assistant/frontend
npm install
npm run dev
```

Open http://localhost:5173/
EOF