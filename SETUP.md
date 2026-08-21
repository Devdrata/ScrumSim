# ScrumSim Setup

This walks through every credential ScrumSim needs. Nothing here requires paid tiers.

## 1. Postgres

Nothing to generate — `docker-compose up -d postgres` starts a local Postgres with the
credentials already wired into `backend/.env.example`.

## 2. Backend secrets

```bash
cd backend
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"   # -> JWT_SECRET
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # -> CREDENTIAL_ENCRYPTION_KEY
```

Paste both values into `backend/.env`.

## 3. Groq API key (LLM provider)

1. Go to https://console.groq.com/keys and sign in (free).
2. Click **Create API Key**, name it `scrumsim-dev`, copy the key.
3. Put it in `backend/.env` as `GROQ_API_KEY`.

Groq's free tier is rate-limited but enough for development. `GROQ_MODEL` defaults to
`llama-3.3-70b-versatile`; swap to any model listed at https://console.groq.com/docs/models.

## 4. GitHub (Personal Access Token)

1. Go to https://github.com/settings/personal-access-tokens/new (fine-grained token).
2. Give it a name (`scrumsim-dev`), set an expiration.
3. Under **Repository access**, choose the specific repo(s) ScrumSim should read.
4. Under **Permissions -> Repository permissions**, set:
   - `Contents`: Read-only
   - `Pull requests`: Read-only
   - `Issues`: Read-only
5. Generate the token and copy it — you paste it into the ScrumSim **Integrations Settings**
   page per-organization (not into `.env`; it's stored encrypted in Postgres).

## 5. Jira (Atlassian API token)

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens.
2. Click **Create API token**, name it `scrumsim-dev`, copy it.
3. You'll also need:
   - Your Atlassian site URL, e.g. `https://yourteam.atlassian.net`
   - The email address of your Atlassian account
4. Enter site URL + email + token together in the ScrumSim Integrations Settings page.

## 6. Slack (Bot token)

1. Go to https://api.slack.com/apps -> **Create New App** -> **From scratch**.
2. Name it `ScrumSim`, pick your workspace.
3. In **OAuth & Permissions**, under **Bot Token Scopes**, add:
   - `chat:write`
   - `channels:read`
4. Click **Install to Workspace**, approve.
5. Copy the **Bot User OAuth Token** (starts with `xoxb-`).
6. Invite the bot to the channel it should post to: `/invite @ScrumSim` in that Slack channel.
7. Enter the bot token + target channel name in the ScrumSim Integrations Settings page.

## 7. Running everything

```bash
# Postgres
docker-compose up -d postgres

# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173, sign up an organization, and add your GitHub/Jira/Slack
credentials under **Settings -> Integrations**.
