# ScrumSim

ScrumSim is an agentic AI Scrum Master: it plans sprints, summarizes stand-ups, prioritizes
the backlog, and facilitates retrospectives by reading real signal from GitHub, Jira, and
Slack. Agents never write directly to your data — every agent action is a **draft** a human
approves, edits, or rejects.

## Stack

- **Backend**: FastAPI + SQLAlchemy + Postgres, JWT auth, multi-tenant (organizations/teams).
- **Agents**: LangGraph orchestrating four agent nodes (planner, standup, backlog, retro) on
  top of a pluggable LangChain chat model (Groq by default, swappable to any LangChain
  provider via `LLM_PROVIDER`).
- **Integrations**: GitHub (PAT), Jira (API token), Slack (bot token) — real API calls, no
  mocked data.
- **Frontend**: React + TypeScript + Vite + Tailwind + React Query.

## Getting started

See [SETUP.md](./SETUP.md) for generating every credential (Groq, GitHub, Jira, Slack) and
running the app locally.

## Project layout

```
backend/   FastAPI app, SQLAlchemy models, LangGraph agents, integration clients
frontend/  React dashboard
docker-compose.yml   Local Postgres
SETUP.md   Credential + local run walkthrough
```

## Human oversight

Every agent run is stored in `agent_runs` as a pending proposal. Nothing lands in the real
backlog/sprint/standup tables until a user approves it via `POST /agents/runs/{id}/approve`
(or rejects it). This is enforced at the API layer, not just in the UI.
