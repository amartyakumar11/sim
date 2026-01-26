# Digital Twin Simulation Sandbox

Production-grade digital twin for EV battery swap networks.

## Team Rules

- Nobody commits directly to main
- Every task happens in a feature branch
- Every PR requires review
- Master context must be updated before architecture changes
- Docker is the source of truth

## File Ownership

**You own:**
- backend/simulation/
- backend/schemas/
- backend/configs/
- digital_twin_master_context.md

**Friend owns:**
- frontend/
- backend/api/
- docker-compose.yml
- backend/tasks.py

**Shared (coordinate first):**
- backend/models/
- backend/database/
- backend/requirements.txt

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```
