import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.integrations import github_client, jira_client
from app.integrations.exceptions import IntegrationError
from app.models.backlog_item import BacklogItem, BacklogItemStatus
from app.models.skill_stat import UserSkillStat
from app.models.sprint import Sprint, SprintStatus
from app.models.user import User

VELOCITY_SPRINT_WINDOW = 5


def gather_backlog(db: Session, project_id: uuid.UUID) -> list[dict]:
    items = db.query(BacklogItem).filter(BacklogItem.project_id == project_id).all()
    return [
        {
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "status": item.status.value,
            "item_type": item.item_type.value,
            "parent_id": str(item.parent_id) if item.parent_id else None,
            "impact_score": item.impact_score,
            "deadline": item.deadline.isoformat() if item.deadline else None,
            "priority_rank": item.priority_rank,
            "story_points": item.story_points,
            "required_skills": item.required_skills,
        }
        for item in items
    ]


def gather_org_members(db: Session, org_id: uuid.UUID, sprint_id: uuid.UUID | None = None) -> list[dict]:
    members = db.query(User).filter(User.org_id == org_id).all()
    stats_by_user: dict[uuid.UUID, list[dict]] = {}
    for stat in db.query(UserSkillStat).join(User, User.id == UserSkillStat.user_id).filter(User.org_id == org_id):
        stats_by_user.setdefault(stat.user_id, []).append(
            {
                "skill": stat.skill,
                "completed_task_count": stat.completed_task_count,
                "completed_story_points": stat.completed_story_points,
            }
        )

    # Points already committed to each member *in this sprint* from earlier approved plans,
    # so the planner can spread new assignments instead of piling everything on whoever
    # matched best on the first few items.
    load_by_user: dict[uuid.UUID, int] = {}
    if sprint_id is not None:
        existing = (
            db.query(BacklogItem)
            .filter(BacklogItem.sprint_id == sprint_id, BacklogItem.status != BacklogItemStatus.DONE)
            .all()
        )
        for item in existing:
            if item.assignee_id is not None:
                load_by_user[item.assignee_id] = load_by_user.get(item.assignee_id, 0) + (item.story_points or 0)

    return [
        {
            "id": str(member.id),
            "full_name": member.full_name,
            "email": member.email,
            "declared_skills": member.skills,
            "demonstrated_skills": stats_by_user.get(member.id, []),
            "current_sprint_points": load_by_user.get(member.id, 0),
        }
        for member in members
    ]


def gather_sprint_capacity(db: Session, sprint_id: uuid.UUID) -> dict:
    sprint = db.get(Sprint, sprint_id)
    return {"capacity_points": sprint.capacity_points if sprint else None}


def gather_velocity(db: Session, project_id: uuid.UUID) -> float | None:
    completed_sprints = (
        db.query(Sprint)
        .filter(Sprint.project_id == project_id, Sprint.status == SprintStatus.COMPLETED)
        .order_by(Sprint.created_at.desc())
        .limit(VELOCITY_SPRINT_WINDOW)
        .all()
    )
    if not completed_sprints:
        return None
    totals = []
    for sprint in completed_sprints:
        items = db.query(BacklogItem).filter(BacklogItem.sprint_id == sprint.id).all()
        done = [i for i in items if i.status == BacklogItemStatus.DONE]
        totals.append(sum((i.story_points if i.story_points is not None else 1) for i in done))
    return round(sum(totals) / len(totals), 1)


def gather_recent_github_activity(github_creds: dict | None, since: datetime) -> dict:
    if not github_creds:
        return {"available": False}
    try:
        commits = github_client.get_recent_commits(github_creds["token"], github_creds["repo"], since=since)
        prs = github_client.get_recent_pull_requests(github_creds["token"], github_creds["repo"])
    except IntegrationError as exc:
        return {"available": False, "error": str(exc)}
    return {"available": True, "commits": commits, "pull_requests": prs}


def gather_recent_jira_activity(jira_creds: dict | None) -> dict:
    if not jira_creds:
        return {"available": False}
    try:
        issues = jira_client.get_recent_issues(
            jira_creds["site_url"], jira_creds["email"], jira_creds["api_token"], jira_creds["project_key"]
        )
    except IntegrationError as exc:
        return {"available": False, "error": str(exc)}
    return {"available": True, "issues": issues}


def gather_sprint_metrics(db: Session, sprint_id: uuid.UUID) -> dict:
    sprint = db.get(Sprint, sprint_id)
    items = db.query(BacklogItem).filter(BacklogItem.sprint_id == sprint_id).all()
    done = [i for i in items if i.status.value == "done"]
    return {
        "sprint_name": sprint.name if sprint else None,
        "sprint_status": sprint.status.value if sprint else None,
        "total_items": len(items),
        "completed_items": len(done),
        "completion_rate": round(len(done) / len(items), 2) if items else None,
        "items": [{"title": i.title, "status": i.status.value} for i in items],
    }
