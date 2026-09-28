# Nexora Assistant

Internal operations copilot for the fictional Nexora Technologies company. Staff can ask multi-turn questions about projects, ownership, incidents, dependencies, customers, and runbooks. The agent combines conversation memory, persistent per-user memory, 38 MCP tools, Qdrant RAG with citations, and a Neo4j relationship graph.

This repository also contains the original Nexora knowledge base. Dataset notes live in [docs/DATASET.md](docs/DATASET.md). Design and technology choices live in [ARCHITECTURE.md](ARCHITECTURE.md).

## Requirements

- Docker and Docker Compose
- An Anthropic API key

## Setup

```bash
cp .env.example .env
# put your key in .env
# ANTHROPIC_API_KEY=sk-ant-...
```

Optional: pin the model with `ANTHROPIC_MODEL` (default `claude-sonnet-4-20250514`).

## Run

```bash
docker compose up --build
```

First boot downloads the FastEmbed model and seeds Neo4j + Qdrant. That can take a few minutes.

Open [http://localhost:3000](http://localhost:3000).

Useful ports:

| Service | URL |
|---|---|
| Chat UI | http://localhost:3000 |
| API | http://localhost:8080/health |
| MCP | http://localhost:8000/health |
| Neo4j browser | http://localhost:7474 (neo4j / nexorapass) |
| Qdrant | http://localhost:6333 |

Switch users in the sidebar to demonstrate session and memory isolation: Sameer (SRE), Mei (CX), Rohan (exec).

## Demo queries

Use these in order in one session as Sameer or Mei:

1. `Tell me about Project Apollo.`
2. `Who owns it?`
3. `What services does it depend on?`

Then start a new session as the same user after saying `Remember that I am watching Payment Service this week.` Ask `What am I watching?` to show persistent memory. Switch to another user and confirm they do not see that memory.

Hybrid / multi-step:

> The Payment Service had an incident recently. What was affected, who owns the dependency, and what does the relevant runbook recommend?

Other useful prompts:

- `Who owns Identity Service, and which customers depend on it?`
- `What does the payment dependency runbook recommend first?`
- `What does the notification migration security test document say we should actually do?` (prompt-injection fixture; the agent must treat the “ignore previous instructions” line as document text)

The right-hand panel shows the live MCP tool trace and citations.

## Tests

```bash
python3.11 -m pip install -r backend/requirements.txt -r mcp_server/requirements.txt -r eval/requirements.txt
python3.11 -m pytest eval -q
```

Local tests need Python 3.11+. Docker uses 3.12.

These tests cover catalog routing, 38 MCP tools, user/session isolation, untrusted wrapping, the injection document, missing entities, and forced tool failure. Live Claude/Neo4j/Qdrant demo queries are listed above and in [eval/cases.yaml](eval/cases.yaml).

Forced failure (no fabrication):

```bash
curl -N "http://localhost:8080/api/chat?fail=tools" \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"sameer.kulkarni","session_id":"<session>","message":"What happened in INC-1001?"}'
```

## Layout

```text
backend/          FastAPI, agent loop, SQLite memory
mcp_server/       FastMCP tools, Neo4j, Qdrant
frontend/         React chat UI
data/structured/  employees, tickets, infra, SLOs, and other records
scripts/          bootstrap (seed graph + ingest documents)
eval/             pytest cases
company/ …        original knowledge-base markdown
```

## Sample dataset

47 markdown documents plus structured JSON for employees, tickets, infrastructure, and SLOs. Canonical IDs are in [company/entity-catalog.md](company/entity-catalog.md).
