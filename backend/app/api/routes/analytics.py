import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_org_project
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.backlog_item import BacklogItem, BacklogItemStatus
from app.models.sprint import Sprint, SprintStatus
from app.models.user import User
from app.schemas.analytics import BottleneckItem, BurndownPoint, ProjectAnalytics, SprintBurndown

router = APIRouter(tags=["analytics"])

BOTTLENECK_THRESHOLD_DAYS = 3
VELOCITY_SPRINT_WINDOW = 5
MAX_BURNDOWN_DAYS = 90


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _points(item: BacklogItem) -> int:
    return item.story_points if item.story_points is not None else 1


def _build_burndown_series(items: list[BacklogItem], start: date, end: date) -> list[BurndownPoint]:
    total = sum(_points(i) for i in items)
    done_items = [(i, _as_aware(i.updated_at).date()) for i in items if i.status == BacklogItemStatus.DONE]

    series: list[BurndownPoint] = []
    day = start
    count = 0
    while day <= end and count < MAX_BURNDOWN_DAYS:
        completed_by_day = sum(_points(i) for i, done_date in done_items if done_date <= day)
        series.append(BurndownPoint(date=day, remaining_points=max(total - completed_by_day, 0)))
        day += timedelta(days=1)
        count += 1
    return series


def _sprint_points(db: Session, sprint_id: uuid.UUID, only_done: bool) -> int:
    items = db.query(BacklogItem).filter(BacklogItem.sprint_id == sprint_id).all()
    if only_done:
        items = [i for i in items if i.status == BacklogItemStatus.DONE]
    return sum(_points(i) for i in items)


@router.get("/projects/{project_id}/analytics", response_model=ProjectAnalytics)
def get_project_analytics(
    project_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ProjectAnalytics:
    project = get_org_project(db, current_user, project_id)

    active_sprint = (
        db.query(Sprint).filter(Sprint.project_id == project.id, Sprint.status == SprintStatus.ACTIVE).first()
    )
    burndown = None
    if active_sprint is not None:
        items = db.query(BacklogItem).filter(BacklogItem.sprint_id == active_sprint.id).all()
        done = [i for i in items if i.status == BacklogItemStatus.DONE]
        total_points = sum(_points(i) for i in items)
        completed_points = sum(_points(i) for i in done)

        series_start = active_sprint.start_date or active_sprint.created_at.date()
        series_end = active_sprint.end_date or date.today()
        series = _build_burndown_series(items, series_start, series_end) if items else []

        burndown = SprintBurndown(
            sprint_id=active_sprint.id,
            sprint_name=active_sprint.name,
            status=active_sprint.status.value,
            total_items=len(items),
            completed_items=len(done),
            completion_rate=round(len(done) / len(items), 2) if items else None,
            capacity_points=active_sprint.capacity_points,
            total_points=total_points,
            completed_points=completed_points,
            burndown_series=series,
        )

    now = datetime.now(timezone.utc)
    stuck_items = (
        db.query(BacklogItem)
        .filter(BacklogItem.project_id == project.id, BacklogItem.status == BacklogItemStatus.IN_PROGRESS)
        .all()
    )
    bottlenecks = []
    for item in stuck_items:
        days = (now - _as_aware(item.updated_at)).total_seconds() / 86400
        if days >= BOTTLENECK_THRESHOLD_DAYS:
            bottlenecks.append(
                BottleneckItem(
                    id=item.id,
                    title=item.title,
                    status=item.status.value,
                    days_in_status=round(days, 1),
                    sprint_id=item.sprint_id,
                )
            )
    bottlenecks.sort(key=lambda b: b.days_in_status, reverse=True)

    completed_sprints = (
        db.query(Sprint)
        .filter(Sprint.project_id == project.id, Sprint.status == SprintStatus.COMPLETED)
        .order_by(Sprint.created_at.desc())
        .limit(VELOCITY_SPRINT_WINDOW)
        .all()
    )
    velocity = None
    if completed_sprints:
        totals = [_sprint_points(db, s.id, only_done=True) for s in completed_sprints]
        velocity = round(sum(totals) / len(totals), 1)

    return ProjectAnalytics(active_sprint=burndown, bottlenecks=bottlenecks, velocity=velocity)
