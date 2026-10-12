# Arch Build AI — Python backend

This repository provides a FastAPI backend for architecture-focused AI chat.

## Endpoints
- `GET /` — service information
- `GET /health` — health check
- `POST /chat` — sends a question to the AI provider
- `GET /docs` — interactive API documentation

## Deploy on Render
1. Upload these files to the **root** of your existing `ARCH-BUILD-AI` GitHub repository.
2. In Render, choose **New + → Blueprint** and connect that repository. Render reads `render.yaml`.
   If Blueprint is unavailable, create a **New Web Service**, choose Python, build command
   `pip install -r requirements.txt`, and start command
   `uvicorn app:app --host 0.0.0.0 --port $PORT`.
3. In Render's Environment settings, add `GROQ_API_KEY` with your secret API key.
4. Deploy, then visit `https://YOUR-SERVICE.onrender.com/health`. It should return JSON with
   `"status":"ok"`. Visit `/docs` to test `/chat`.

## AI API key
The backend uses the Groq API. Create an API key in the Groq Console and add it only as the
`GROQ_API_KEY` environment variable in Render. Never paste a secret key into frontend HTML,
GitHub, screenshots, or chat messages. Provider availability, models, free quotas, and terms
can change; review the provider's current terms.

## Connect your existing frontend
Send a POST request to `https://YOUR-SERVICE.onrender.com/chat` with JSON:
`{"message":"Explain one-point perspective in architecture"}`

The response format is:
`{"answer":"..."}`

This backend does not yet process image uploads. That can be added in a later version.
