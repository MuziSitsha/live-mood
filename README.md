# Live Mood Architect

Generate short, supportive affirmations based on how someone is feeling.

## Stack
- Frontend: Next.js
- Backend: FastAPI (Python)
- AI: Hugging Face Inference Router (chat-completions)

## Local Development

### Backend
1) Create and activate a virtual environment.
2) Install dependencies:
```bash
python -m pip install -r backend/requirements.txt
```
3) Set environment variables:
```bash
HUGGING_FACE_API_KEY=your_hf_key_here
HUGGING_FACE_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
HUGGING_FACE_FALLBACK_MODELS=Qwen/Qwen2.5-7B-Instruct
ALLOWED_ORIGINS=http://localhost:3000
DEBUG=false
```
4) Run the API:
```bash
uvicorn backend.main:app --reload
```

### Backend Tests + Lint
```bash
pytest
ruff check .
```

### Frontend
1) Install dependencies:
```bash
npm install
```
2) Create a `.env.local` in `frontend/`:
```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```
3) Run the app:
```bash
npm run dev
```

### Frontend Lint
```bash
npm run lint
```

## Environment Variables

### Backend
- `HUGGING_FACE_API_KEY` (required)
- `HUGGING_FACE_MODEL` (optional, default: `meta-llama/Meta-Llama-3-8B-Instruct`)
- `HUGGING_FACE_FALLBACK_MODELS` (optional, comma-separated list)
- `ALLOWED_ORIGINS` (optional, comma-separated list of frontend origins)
- `DEBUG` (optional, default: `false`)

### Frontend
- `NEXT_PUBLIC_API_BASE_URL` (required for deployment)

## Deployment

### Backend (Render/Railway/PythonAnywhere)
1) Deploy `backend/` as a Python web service.
2) Set `HUGGING_FACE_API_KEY` and `ALLOWED_ORIGINS` to your frontend URL.
3) Start command:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Frontend (Vercel/Netlify)
1) Deploy `frontend/` as a Next.js app.
2) Set `NEXT_PUBLIC_API_BASE_URL` to your backend URL.

## Live URLs
- Frontend: <ADD_LIVE_FRONTEND_URL>
- Backend: <ADD_LIVE_BACKEND_URL>

## What I Would Improve With More Time
- Add analytics for completion latency and error rates.
- Add rate limiting and request tracing for production.
- Add e2e tests for the full request flow.