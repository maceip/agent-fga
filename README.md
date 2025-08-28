# **agent-fga**
agent authorization demo, a marketplace for delegated access to emails



<img width="239" height="238" alt="faces" src="https://github.com/user-attachments/assets/8397fc54-fef3-4853-b3db-9c9e195fd10f" />



## Tech Stack

- **Authorization**: OpenFGA
- **Backend**: FastAPI, Python
- **Frontend**: Next.js, React
- **Database**: PostgreSQL, Prisma ORM
- **Authentication**: Google OAuth 2.0
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
