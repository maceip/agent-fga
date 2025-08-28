from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from prisma import Prisma
import httpx
import os

# --- Configuration ---
DATABASE_URL = os.environ.get("DATABASE_URL")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
SESSION_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY")
PERSONAL_AGENT_URL = os.environ.get("PERSONAL_AGENT_URL")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://mcp_server:8090")

app = FastAPI()
db = Prisma()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send'}
)

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

@app.get('/auth/google')
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/auth/google/callback')
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.parse_id_token(request, token)
    
    user = await db.user.upsert(
        where={'googleSub': user_info['sub']},
        data={
            'create': {
                'googleSub': user_info['sub'],
                'email': user_info['email'],
                'accessToken': token['access_token'],
                'refreshToken': token.get('refresh_token'),
            },
            'update': {
                'accessToken': token['access_token'],
                'refreshToken': token.get('refresh_token'),
            }
        }
    )
    request.session['user_id'] = user.id
    return RedirectResponse(url='http://localhost:3000')

@app.get('/auth/status')
def auth_status(request: Request):
    return {"authenticated": 'user_id' in request.session}

@app.get('/agents')
async def get_available_agents():
    """Fetch all available agents from MCP server"""
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{MCP_SERVER_URL}/agents")
            res.raise_for_status()
            return res.json()
    except Exception as e:
        return {"agents": [], "error": str(e)}

@app.get('/agents/{agent_id}')
async def get_agent_card(agent_id: str):
    """Fetch specific agent card from MCP server"""
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{MCP_SERVER_URL}/agents/{agent_id}")
            res.raise_for_status()
            return res.json()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Agent not found: {str(e)}")

@app.post('/invoke-agent')
async def invoke_agent(request: Request):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="User not authenticated")

    user = await db.user.find_unique(where={'id': request.session['user_id']})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    body = await request.json()
    agent_id = body.get("agent_id")

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{PERSONAL_AGENT_URL}/delegate-and-run",
            json={
                "google_sub": user.googleSub,
                "access_token": user.accessToken,
                "contracted_agent_id": agent_id
            },
            timeout=30.0
        )
    res.raise_for_status()
    return res.json()