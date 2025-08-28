from fastapi import FastAPI, Request
import httpx

app = FastAPI()
PERSONAL_AGENT_PROXY_URL = "http://personal_agent:8002/proxy/gmail/read"

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