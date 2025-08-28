# AGENTS.md

## Project Overview

agentaccess is an agent authorization demo showcasing secure delegated access to Gmail through a marketplace architecture. The system uses OpenFGA for fine-grained authorization control between multiple agents.

## Setup Commands

```bash
# install python dependencies
uv sync

# install frontend dependencies
cd frontend && npm install

# start all services
docker compose up --build -d

# initialize OpenFGA (see README for full commands)
./scripts/setup-openfga.sh  # if you create this script
```

## Development Commands

```bash
# backend development (any service)
cd [service_name]
uvicorn main:app --reload --port [port]

# frontend development
cd frontend
npm run dev

# view logs
docker compose logs -f [service_name]

# restart specific service
docker compose restart [service_name]
```

## Code Style

### Python
- use FastAPI for all backend services
- async/await for all IO operations
- type hints for function parameters and returns
- no class-based views, use function decorators
- handle errors explicitly, never silently fail

### JavaScript
- functional React components only
- Zustand for state management
- no semicolons unless required
- single quotes for strings
- inline styles for demo simplicity

### General
- keep it simple - this is a demo
- security first - validate all inputs
- explicit over implicit

## Testing Instructions

```bash
# python tests (when added)
pytest

# javascript tests (when added)
npm test

# manual testing flow
1. start all services
2. login with Google OAuth
3. test good agent - should summarize emails
4. test malicious agent - should show phishing attempt
5. verify OpenFGA blocks unauthorized actions
```

## Architecture Notes

- **Personal Agent** is the trust boundary - all Gmail API calls go through it
- **OpenFGA** decides who can do what - check permissions before actions
- agents get temporary permissions that auto-revoke after task completion
- access tokens never leave the personal agent
- each service runs in isolation via Docker

## Common Issues

- if OpenFGA store ID missing: run the setup commands in README
- if OAuth fails: check Google Console redirect URIs
- if containers won't start: check port conflicts (5432, 8001-8004, 8080-8081, 3000)
- if Prisma errors: run `prisma generate` and `prisma db push`

## Security Considerations

- never commit .env files
- rotate OAuth secrets regularly
- access tokens are temporary and scoped
- all agent actions are logged
- OpenFGA policies are append-only audit trail

## PR Guidelines

- keep changes focused and small
- update AGENTS.md if you change setup/commands
- test both agents before submitting
- include OpenFGA model changes in separate commits
- describe security implications in PR description