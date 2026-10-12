import os
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Arch Build AI API",
    description="Architecture-focused AI backend for Arch Build AI.",
    version="1.0.0",
)

# For the first test, allow requests from any website. Once your frontend is deployed,
# replace ["*"] with your website's exact origin for better security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    history: Optional[list[dict[str, str]]] = None


class ChatResponse(BaseModel):
    answer: str


SYSTEM_PROMPT = """
You are Arch Build AI, a helpful AI assistant focused on architecture, building design,
architectural drawing, floor-plan concepts, materials, sustainability, construction basics,
architectural history, and NATA-style practice.

Be clear and encouraging. For design ideas, explain that they are concepts and must be
checked by a qualified architect/engineer before construction. Do not claim that a plan is
structurally safe or code-compliant without professional verification. If asked unrelated
questions, briefly help when appropriate but guide the conversation back to architecture.
Never invent dimensions from an image or claim to have inspected an image that was not sent.
"""

@app.get("/")
def root():
    return {
        "name": "Arch Build AI API",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "Arch Build AI", "ai_configured": bool(os.getenv("GROQ_API_KEY"))}


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI is not configured yet. Add GROQ_API_KEY in your Render environment variables.",
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if payload.history:
        # Keep only recent, well-formed user/assistant turns.
        for item in payload.history[-8:]:
            role = item.get("role")
            content = item.get("content")
            if role in ("user", "assistant") and isinstance(content, str) and content.strip():
                messages.append({"role": role, "content": content[:4000]})
    messages.append({"role": "user", "content": payload.message})

    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 1200,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
        if response.status_code >= 400:
            # Don't expose the API key or provider response headers.
            detail = "The AI provider returned an error. Check your API key, model name, and usage limits."
            if response.status_code in (401, 403):
                detail = "The AI API key was rejected. Check the GROQ_API_KEY value in Render."
            elif response.status_code == 429:
                detail = "The AI service is busy or its free usage limit has been reached. Try again later."
            raise HTTPException(status_code=502, detail=detail)

        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip()
        return ChatResponse(answer=answer or "I couldn't generate an answer. Please try again.")
    except HTTPException:
        raise
    except (httpx.TimeoutException, httpx.RequestError):
        raise HTTPException(status_code=504, detail="The AI service timed out. Please try again.")
    except (KeyError, IndexError, ValueError):
        raise HTTPException(status_code=502, detail="The AI service returned an unexpected response.")
