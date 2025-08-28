from fastapi import FastAPI, Request
import httpx

app = FastAPI()
PERSONAL_AGENT_PROXY_URL = "http://personal_agent:8002/proxy/gmail/read"

# Agent Card for discovery
AGENT_CARD = {
    "agent_id": "good_agent",
    "name": "Email Summarizer Pro",
    "description": "Professional email summarization service",
    "version": "1.0.0",
    "capabilities": [
        "email_summarization",
        "inbox_insights",
        "activity_analysis"
    ],
    "tools": ["email_summarizer"],
    "endpoints": {
        "execute": "http://good_agent:8003/execute_task",
        "status": "http://good_agent:8003/status"
    },
    "metadata": {
        "trust_level": 3,
        "category": "productivity",
        "verified": True
    }
}

@app.get("/agent_card")
async def get_agent_card():
    """Return agent card for discovery"""
    return AGENT_CARD

@app.post("/")
async def get_email_summary(request: Request):
    body = await request.json()
    user_id = body.get("user_id")
    
    async with httpx.AsyncClient() as client:
        res = await client.post(PERSONAL_AGENT_PROXY_URL, json={
            "user_id": user_id,
            "agent_id": "good_agent"
        })
    res.raise_for_status()
    
    emails = res.json().get('messages', [])
    summary = f"Successfully read {len(emails)} emails. Looks like a normal day!"
    return {"summary": summary}