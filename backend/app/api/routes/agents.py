import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.agents.nodes import backlog as backlog_agent
from app.agents.nodes import planner as planner_agent
from app.agents.nodes import retro as retro_agent
from app.agents.nodes import srs_intake as srs_intake_agent
from app.agents.nodes import standup as standup_agent
from app.api.deps import get_org_project, get_org_sprint
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.integrations.store import get_org_credential
from app.models.agent_run import AgentRun, AgentRunStatus, AgentType
from app.models.backlog_item import BacklogItem, BacklogItemStatus, BacklogItemType
from app.models.integration_credential import IntegrationProvider
from app.models.retro_entry import RetroCategory, RetroEntry
from app.models.standup_entry import StandupAuthor, StandupEntry
from app.models.user import User
from app.schemas.agent import (
    AgentRunOut,
    BacklogRunRequest,
    PlannerRunRequest,
    RetroRunRequest,
    StandupRunRequest,
)

router = APIRouter(prefix="/agents", tags=["agents"])

MAX_SRS_CHARS = 200_000
SUPPORTED_SRS_EXTENSIONS = (".txt", ".md", ".pdf")


def _extract_srs_text(filename: str, content: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        from io import BytesIO

        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif name.endswith((".txt", ".md")):
        text = content.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_SRS_EXTENSIONS)}",
        )

    if len(text) > MAX_SRS_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document too large ({len(text)} chars, max {MAX_SRS_CHARS}). Split it and import in parts.",
        )
    if not text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No extractable text found in document")
    return text


@router.post("/planner/run", response_model=AgentRunOut, status_code=status.HTTP_201_CREATED)
def run_planner(
    payload: PlannerRunRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AgentRun:
    project = get_org_project(db, current_user, payload.project_id)
    sprint = get_org_sprint(db, current_user, payload.sprint_id)
    if sprint.project_id != project.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sprint does not belong to project")

    result = planner_agent.run(db, current_user.org_id, project.id, sprint.id)
    run = AgentRun(
        org_id=current_user.org_id,
        project_id=project.id,
        agent_type=AgentType.PLANNER,
        input_context={"gathered": result["context"], "target_sprint_id": str(sprint.id)},
        proposed_output=result["proposed_output"],
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.post("/srs-intake/run/{project_id}", response_model=AgentRunOut, status_code=status.HTTP_201_CREATED)
async def run_srs_intake(
    project_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AgentRun:
    project = get_org_project(db, current_user, project_id)
    content = await file.read()
    srs_text = _extract_srs_text(file.filename or "", content)

    result = srs_intake_agent.run(srs_text)
    run = AgentRun(
        org_id=current_user.org_id,
        project_id=project.id,
        agent_type=AgentType.SRS_INTAKE,
        input_context={"source_filename": file.filename},
        proposed_output=result["proposed_output"],
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.post("/standup/run", response_model=AgentRunOut, status_code=status.HTTP_201_CREATED)
def run_standup(
    payload: StandupRunRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AgentRun:
    project = get_org_project(db, current_user, payload.project_id)
    github_creds = get_org_credential(db, current_user.org_id, IntegrationProvider.GITHUB)
    jira_creds = get_org_credential(db, current_user.org_id, IntegrationProvider.JIRA)

    result = standup_agent.run(db, project.id, github_creds, jira_creds)
    run = AgentRun(
        org_id=current_user.org_id,
        project_id=project.id,
        agent_type=AgentType.STANDUP,
        input_context={"gathered": result["context"]},
        proposed_output=result["proposed_output"],
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.post("/backlog/run", response_model=AgentRunOut, status_code=status.HTTP_201_CREATED)
def run_backlog(
    payload: BacklogRunRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AgentRun:
    project = get_org_project(db, current_user, payload.project_id)
    result = backlog_agent.run(db, project.id)
    run = AgentRun(
        org_id=current_user.org_id,
        project_id=project.id,
        agent_type=AgentType.BACKLOG,
        input_context={"gathered": result["context"]},
        proposed_output=result["proposed_output"],
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.post("/retro/run", response_model=AgentRunOut, status_code=status.HTTP_201_CREATED)
def run_retro(
    payload: RetroRunRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AgentRun:
    sprint = get_org_sprint(db, current_user, payload.sprint_id)
    result = retro_agent.run(db, sprint.id)
    run = AgentRun(
        org_id=current_user.org_id,
        project_id=sprint.project_id,
        agent_type=AgentType.RETRO,
        input_context={"gathered": result["context"], "target_sprint_id": str(sprint.id)},
        proposed_output=result["proposed_output"],
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/runs", response_model=list[AgentRunOut])
def list_agent_runs(
    project_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AgentRun]:
    query = db.query(AgentRun).filter(AgentRun.org_id == current_user.org_id)
    if project_id is not None:
        query = query.filter(AgentRun.project_id == project_id)
    return query.order_by(AgentRun.created_at.desc()).all()


def _get_org_run(db: Session, current_user: User, run_id: uuid.UUID) -> AgentRun:
    run = db.get(AgentRun, run_id)
    if run is None or run.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    return run


def _apply_agent_run(db: Session, run: AgentRun) -> None:
    output = run.proposed_output

    if run.agent_type == AgentType.PLANNER:
        target_sprint_id = uuid.UUID(run.input_context["target_sprint_id"])
        for rec in output.get("recommended_items", []):
            item = db.get(BacklogItem, uuid.UUID(rec["backlog_item_id"]))
            if item is not None and item.status != BacklogItemStatus.DONE:
                item.sprint_id = target_sprint_id
                item.status = BacklogItemStatus.IN_SPRINT

                assignee_user_id = rec.get("assignee_user_id")
                if assignee_user_id:
                    assignee = db.get(User, uuid.UUID(assignee_user_id))
                    if assignee is not None and assignee.org_id == run.org_id:
                        item.assignee_id = assignee.id

    elif run.agent_type == AgentType.STANDUP:
        entry = StandupEntry(
            project_id=run.project_id,
            author=StandupAuthor.AGENT,
            content=output.get("summary", ""),
            blockers="; ".join(output.get("blockers", [])) or None,
        )
        db.add(entry)

    elif run.agent_type == AgentType.BACKLOG:
        for rank, item_id in enumerate(output.get("ordered_item_ids", []), start=1):
            item = db.get(BacklogItem, uuid.UUID(item_id))
            if item is not None:
                item.priority_rank = rank

    elif run.agent_type == AgentType.RETRO:
        target_sprint_id = uuid.UUID(run.input_context["target_sprint_id"])
        for content in output.get("went_well", []):
            db.add(RetroEntry(sprint_id=target_sprint_id, category=RetroCategory.WENT_WELL, content=content))
        for content in output.get("went_wrong", []):
            db.add(RetroEntry(sprint_id=target_sprint_id, category=RetroCategory.WENT_WRONG, content=content))
        for content in output.get("action_items", []):
            db.add(RetroEntry(sprint_id=target_sprint_id, category=RetroCategory.ACTION_ITEM, content=content))

    elif run.agent_type == AgentType.SRS_INTAKE:
        level_to_type = {1: BacklogItemType.EPIC, 2: BacklogItemType.STORY, 3: BacklogItemType.TASK}
        # Reconstruct the tree purely from (level, sequence) - the LLM emits a flat, ordered
        # list rather than inventing/cross-referencing ids, which turned out to be far more
        # reliable for structured-output tool calling than asking it to link parent ids itself.
        last_id_by_level: dict[int, uuid.UUID] = {}

        for draft in output.get("items", []):
            level = draft.get("level", 3)
            if level not in level_to_type:
                level = 3
            parent_id = last_id_by_level.get(level - 1) if level > 1 else None

            new_item = BacklogItem(
                project_id=run.project_id,
                parent_id=parent_id,
                title=draft["title"],
                description=draft.get("description") or None,
                item_type=level_to_type[level],
                story_points=draft.get("story_points"),
                required_skills=draft.get("required_skills", []),
                acceptance_criteria=draft.get("acceptance_criteria") or None,
            )
            db.add(new_item)
            db.flush()

            last_id_by_level[level] = new_item.id
            for deeper_level in list(last_id_by_level):
                if deeper_level > level:
                    del last_id_by_level[deeper_level]


@router.post("/runs/{run_id}/approve", response_model=AgentRunOut)
def approve_agent_run(
    run_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AgentRun:
    run = _get_org_run(db, current_user, run_id)
    if run.status != AgentRunStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent run already reviewed")

    _apply_agent_run(db, run)
    run.status = AgentRunStatus.APPROVED
    run.reviewed_by = current_user.id
    run.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


@router.post("/runs/{run_id}/reject", response_model=AgentRunOut)
def reject_agent_run(
    run_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AgentRun:
    run = _get_org_run(db, current_user, run_id)
    if run.status != AgentRunStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agent run already reviewed")

    run.status = AgentRunStatus.REJECTED
    run.reviewed_by = current_user.id
    run.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run
