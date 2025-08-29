# **agent-fga**
agent authorization demo, a marketplace for delegated access to emails



<img width="239" height="238" alt="faces" src="https://github.com/user-attachments/assets/8397fc54-fef3-4853-b3db-9c9e195fd10f" />



## Tech Stack

- **Authorization**: OpenFGA
- **Backend**: FastAPI, Python
- **Frontend**: Next.js, React
- **Database**: PostgreSQL, Prisma ORM
- **Authentication**: Google OAuth 2.0
- **Agent Communication**: Google Agent Developer Kit (ADK) & Agent-to-Agent (A2A) Protocol
- **Agent Registry**: MCP (Model Context Protocol) Server
- **Container**: Docker, Docker Compose
- **Package Management**: uv (Python), npm (JavaScript)

## Architecture

- **Frontend**: web interface for agent selection (`localhost:3000`)
- **Marketplace Backend**: OAuth handler and token storage (`localhost:8001`)
- **Personal Agent**: trusted proxy managing OpenFGA permissions (`localhost:8002`)
- **Good Agent**: legitimate email summarizer (`localhost:8003`)
- **Malicious Agent**: demonstrates permission abuse (`localhost:8004`)
- **OpenFGA**: authorization server (`localhost:8080`)
- **PostgreSQL**: persistent storage

## Agent Communication Flow

This system demonstrates Google's **Agent Developer Kit (ADK)** and **Agent-to-Agent (A2A)** protocol implementation:

### 1. Agent Registration
- Each agent runs its own A2A server on startup
- Agents register their AgentCard with the MCP server
- MCP maintains a registry of all available agents

### 2. Secure Task Execution
When a user selects an agent:

1. **Permission Grant**: Personal Agent grants temporary OpenFGA permission to selected agent
2. **A2A Communication**: Task sent to agent via A2A protocol
3. **Proxied Access**: Agent requests data through Personal Agent (never direct Gmail access)
4. **Authorization Check**: Personal Agent validates permissions via OpenFGA
5. **Data Delivery**: If authorized, Personal Agent fetches Gmail data and returns it
6. **Permission Revocation**: Temporary permissions automatically revoked after task completion

### 3. Security Boundaries

```
┌─────────────────────────────────────────┐
│            User's Trust Domain          │
│  ┌────────────────────────────────┐     │
│  │     Personal Agent             │     │
│  │  - Holds Gmail access token    │     │
│  │  - Controls all permissions    │     │
│  │  - Proxies all Gmail API calls │     │
│  └────────────────────────────────┘     │
└─────────────────────────────────────────┘
                    ↓
            OpenFGA Authorization
                    ↓
┌─────────────────────────────────────────┐
│         Third-Party Agents              │
│  ┌──────────┐        ┌──────────┐       │
│  │Good Agent│        │Malicious │       │
│  │  ✓ Read  │        │  ✓ Read  │       │
│  │  ✗ Send  │        │  ✗ Send  │       │
│  └──────────┘        └──────────┘       │
└─────────────────────────────────────────┘
```

### Key Security Features

- **Token Isolation**: Gmail access tokens never leave Personal Agent
- **Temporary Permissions**: Auto-revoked after task completion  
- **Fine-grained Control**: OpenFGA ensures exact permissions
- **Zero Trust**: Every request authenticated and authorized
- **Principle of Least Privilege**: Agents get minimum required permissions

```mermaid

%%{init: {
  'theme': 'default',
  'fontFamily': 'Helvetica, Arial, sans-serif',
  'fontSize': 8
}}%%
graph TD
    %% ============ Title ============
    title[<b>Agent Marketplace</b>]
    style title fill:#f0f8ff,stroke:#6c8ebf,stroke-width:2px,font-size:12px,color:#191970,font-weight:bold

    %% ============ Subgraphs ============

    subgraph User_Domain["User's Trust Domain"]
        direction TB
        user((User)):::userStyle
        frontend[Frontend<br/>Next.js :3000]:::frontendStyle
        marketplace[Marketplace Backend<br/>:8001]:::backendStyle
        personal_agent[Personal Agent<br/>A2A Server :8002]:::agentStyle
    end

    subgraph Agent_Domain["Third-Party Agents"]
        direction LR
        mcp_server[MCP Server<br/>Agent Registry]:::registryStyle
        good_agent[Good Agent<br/>A2A Server :8003]:::agentStyle
        bad_agent[Malicious Agent<br/>A2A Server :8004]:::badAgentStyle
    end

    subgraph Backend_Services["Backend Services"]
        direction LR
        openfga[OpenFGA<br/>Authorization :8080]:::authzStyle
        postgresql[PostgreSQL Database]:::dbStyle
        google_apis[Google APIs<br/>OAuth + Gmail]:::apiStyle
    end

    %% ============ Flow Edges ============

    user -->|1. Login| frontend
    frontend -->|2. OAuth Flow| marketplace
    marketplace -->|3. Store Tokens| postgresql

    frontend -->|4. Get Agents| mcp_server

    frontend -->|5. Select Agent| personal_agent

    personal_agent -->|6. Grant Permission| openfga

    personal_agent -->|7. A2A Task| good_agent

    good_agent -->|8. Request Data| personal_agent

    personal_agent -->|9. Check Auth| openfga

    personal_agent -->|10. Fetch Gmail| google_apis

    %% Registration (dashed)
    good_agent -. Register .-> mcp_server
    bad_agent -. Register .-> mcp_server

    %% ============ Security Note ============
    note["🔐 Security:\n• Gmail tokens never leave Personal Agent\n• Permissions are temporary & auto-revoked\n• Zero-trust via OpenFGA"]
    style note fill:#fff2cc,stroke:#d6b656,stroke-width:1px,color:#333,font-size:12px

    Backend_Services --> note

    %% ============ Legend (Simple, Compatible) ============
    legend["Legend:
🟨 User Auth (e.g., 1,2,3)
🟩 Agent Discovery (4)
🟥 Task Execution (5,7,8)
🟧 AuthZ Check (6,9)
🟦 Data Flow (10)\n- - Agent Registration"]
    style legend fill:#f5f5f5,stroke:#666,stroke-width:1px,color:#222,font-size:10px

    Agent_Domain --> legend

    %% ============ Styling Classes ============

    classDef userStyle       fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px,color:black;
    classDef frontendStyle   fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px,color:black;
    classDef backendStyle    fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px,color:black;
    classDef agentStyle      fill:#d5e8d4,stroke:#82b366,stroke-width:2px,color:black;
    classDef badAgentStyle   fill:#f8cecc,stroke:#b85450,stroke-width:2px,color:black;
    classDef registryStyle   fill:#fff2cc,stroke:#d6b656,stroke-width:2px,color:black;
    classDef authzStyle      fill:#ffe6cc,stroke:#d79b00,stroke-width:2px,color:black;
    classDef dbStyle         fill:#e1d5e7,stroke:#9673a6,stroke-width:2px,color:black;
    classDef apiStyle        fill:#fff2cc,stroke:#d6b656,stroke-width:2px,color:black;

    %% Domain styling (light background effect)
    style User_Domain fill:#e1d5e7,stroke:#9673a6,stroke-width:2px,fill-opacity:0.1
    style Agent_Domain fill:#f8cecc,stroke:#b85450,stroke-width:2px,fill-opacity:0.1
    style Backend_Services fill:#ffffff,stroke:#ccc,stroke-dasharray:6 4,stroke-width:1px,fill-opacity:0.05
```

## Prerequisites

- Docker & Docker Compose
- Node.js & npm
- Google Cloud Project with OAuth 2.0 credentials

## Setup

**1. Google OAuth**
- create OAuth 2.0 Client ID in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- add `http://localhost:3000` to authorized origins
- add `http://localhost:8001/auth/google/callback` to redirect URIs
- grab your client ID and secret

**2. Environment**
- copy `.env.example` to `.env`
- add your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

**3. Frontend**
```bash
cd frontend
npm install
cd ..
```

**4. Run**

spin up the backend:
```bash
docker-compose up --build -d
```

set up OpenFGA:
```bash
# create store
export FGA_STORE_ID=$(curl -s -X POST http://localhost:8080/stores -H "Content-Type: application/json" -d '{"name": "gmail_marketplace_store"}' | grep -o '"id":"[^"]*' | cut -d'"' -f4)
echo "Created Store ID: $FGA_STORE_ID"

# save store ID
echo "\nOPENFGA_STORE_ID=$FGA_STORE_ID" >> .env

# load authorization model
curl -X POST http://localhost:8080/stores/$FGA_STORE_ID/authorization-models \
  -H "Content-Type: application/json" \
  -d @./openfga_model/gmail_authz.fga

# restart services with new store ID
docker-compose restart personal_agent marketplace_backend
```

start frontend:
```bash
cd frontend
npm run dev
```

## Usage

1. hit http://localhost:3000
2. login with Google
3. select an agent from the marketplace

the good agent reads and summarizes emails. the malicious agent tries to phish you with the same read permission. OpenFGA prevents both from sending emails on your behalf.


![Privacy is Normal](https://img.shields.io/badge/privacy-is%20normal-green)
