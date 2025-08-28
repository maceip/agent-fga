from fastapi import FastAPI, Request, HTTPException
import httpx
import os

# --- Configuration ---
OPENFGA_API_URL = os.environ.get("OPENFGA_API_URL")
OPENFGA_STORE_ID = os.environ.get("OPENFGA_STORE_ID")
GOOD_AGENT_URL = os.environ.get("GOOD_AGENT_URL")
MALICIOUS_AGENT_URL = os.environ.get("MALICIOUS_AGENT_URL")

AGENT_URLS = {
    "good_agent": GOOD_AGENT_URL,
    "malicious_agent": MALICIOUS_AGENT_URL
}

app = FastAPI()
token_storage = {} # In-memory storage for this demo

# Agent Card for discovery
AGENT_CARD = {
    "agent_id": "personal_agent",
    "name": "Personal Gmail Agent",
    "description": "User's trusted agent that manages Gmail permissions and access",
    "version": "1.0.0",
    "capabilities": [
        "gmail_management",
        "permission_control",
        "secure_delegation"
    ],
    "tools": ["gmail_read", "openfga_manage"],
    "endpoints": {
        "execute": "http://personal_agent:8002/execute_task",
        "status": "http://personal_agent:8002/status"
    },
    "metadata": {
        "trust_level": 5,
        "owner": "user",
        "category": "system",
        "verified": True
    }
}

@app.get("/agent_card")
async def get_agent_card():
    """Return agent card for discovery"""
    return AGENT_CARD

async def fga_write(tuples: list = [], deletes: list = []):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{OPENFGA_API_URL}/stores/{OPENFGA_STORE_ID}/write",
            json={"writes": {"tuple_keys": tuples}, "deletes": {"tuple_keys": deletes}}
        )

async def fga_check(user: str, relation: str, object: str) -> bool:
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{OPENFGA_API_URL}/stores/{OPENFGA_STORE_ID}/check",
            json={"tuple_key": {"user": user, "relation": relation, "object": object}}
        )
        return res.json().get("allowed", False)

@app.post("/delegate-and-run")
async def delegate_and_run(request: Request):
    body = await request.json()
    google_sub = body.get("google_sub")
    access_token = body.get("access_token")
    contracted_agent_id = body.get("contracted_agent_id")
    
    user_id = f"user:{google_sub}"
    gmail_object = f"gmail_account:{user_id}"
    agent_object_id = f"agent:{contracted_agent_id}"

    token_storage[user_id] = access_token

    await fga_write(tuples=[{"user": agent_object_id, "relation": "temporary_reader", "object": gmail_object}])
    
    agent_response = {}
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(AGENT_URLS[contracted_agent_id], json={"user_id": user_id})
            res.raise_for_status()
            agent_response = res.json()
    finally:
        await fga_write(deletes=[{"user": agent_object_id, "relation": "temporary_reader", "object": gmail_object}])
        token_storage.pop(user_id, None)

    return agent_response

@app.post("/proxy/gmail/read")
async def proxy_gmail_read(request: Request):
    body = await request.json()
    user_id = body.get("user_id")
    calling_agent_id = body.get("agent_id")

    is_allowed = await fga_check(user=f"agent:{calling_agent_id}", relation="can_read_emails", object=f"gmail_account:{user_id}")
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Forbidden by OpenFGA: Agent cannot read emails.")

    access_token = token_storage.get(user_id)
    if not access_token:
        raise HTTPException(status_code=401, detail="No valid token for user.")

    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        res = await client.get("https://www.googleapis.com/gmail/v1/users/me/messages?maxResults=3", headers=headers)
    return res.json()

@app.post("/proxy/gmail/send")
async def proxy_gmail_send(request: Request):
    body = await request.json()
    user_id = body.get("user_id")
    calling_agent_id = body.get("agent_id")

    is_allowed = await fga_check(user=f"agent:{calling_agent_id}", relation="can_send_emails", object=f"gmail_account:{user_id}")
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Forbidden by OpenFGA: Agent cannot send emails.")
    
    return {"message": "This is a dummy response. If you see this, the check passed."}