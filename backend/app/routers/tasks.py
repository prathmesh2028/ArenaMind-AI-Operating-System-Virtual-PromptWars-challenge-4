"""
Tasks Router
-------------
GET   /tasks          — List tasks (with incident/volunteer filters)
POST  /tasks          — Create a new task (operations staff)
GET   /tasks/{id}     — Single task detail
PATCH /tasks/{id}     — Update task status / re-assign volunteer
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_operations, require_staff
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import Task
from app.schemas.common import PaginatedResponse
from app.schemas.tasks import TaskCreate, TaskOut, TaskUpdate

logger = logging.getLogger("arenamind.routers.tasks")
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "",
    response_model=PaginatedResponse[TaskOut],
    summary="List all tasks with filters",
)
def list_tasks(
    status: Optional[str] = Query(None, description="PENDING | ACCEPTED | COMPLETED"),
    priority: Optional[str] = Query(None),
    incident_id: Optional[str] = Query(None),
    volunteer_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_staff),
):
    query = db.query(Task).order_by(Task.created_at.desc())

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if incident_id:
        query = query.filter(Task.incident_id == incident_id)
    if volunteer_id:
        query = query.filter(Task.volunteer_id == volunteer_id)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.post(
    "",
    response_model=TaskOut,
    status_code=201,
    summary="Dispatch a new task to a volunteer",
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_operations),
):
    task = Task(
        id=str(uuid.uuid4()),
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        incident_id=payload.incident_id,
        volunteer_id=payload.volunteer_id,
        status="PENDING",
        created_at=datetime.now(timezone.utc),
        eta_minutes=payload.eta_minutes,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    logger.info(f"Task {task.id} created for incident {payload.incident_id} by {current_user.email}")
    return task


@router.get(
    "/{task_id}",
    response_model=TaskOut,
    summary="Get a single task by ID",
)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_staff),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundError("Task", task_id)
    return task


@router.patch(
    "/{task_id}",
    response_model=TaskOut,
    summary="Update task status or volunteer assignment",
)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundError("Task", task_id)

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Auto-set completed_at when task moves to COMPLETED
    if payload.status == "COMPLETED" and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)
    logger.info(f"Task {task_id} updated by {current_user.email}: {update_data}")
    return task
