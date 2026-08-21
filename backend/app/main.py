from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    agents,
    analytics,
    auth,
    backlog,
    integrations,
    invites,
    members,
    retros,
    sprints,
    standups,
    teams,
)
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="ScrumSim API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(invites.router)
app.include_router(members.router)
app.include_router(members.me_router)
app.include_router(teams.router)
app.include_router(sprints.router)
app.include_router(backlog.router)
app.include_router(standups.router)
app.include_router(retros.router)
app.include_router(integrations.router)
app.include_router(agents.router)
app.include_router(analytics.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
