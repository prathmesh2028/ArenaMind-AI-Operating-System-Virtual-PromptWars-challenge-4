"""
Volunteer Portal Router
------------------------
Volunteer-facing task management endpoints.

GET   /volunteer/tasks             — My assigned tasks (sorted by priority)
PATCH /volunteer/tasks/{id}/accept — Accept a task dispatch
PATCH /volunteer/tasks/{id}/complete — Mark a task as completed
GET   /volunteer/notifications     — My unread notifications
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_staff
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import Notification, Task
from app.schemas.tasks import TaskOut

logger = logging.getLogger("arenamind.routers.volunteer")
router = APIRouter(prefix="/volunteer", tags=["Volunteer Portal"])

PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


@router.get(
    "/tasks",
    response_model=list[TaskOut],
    summary="Get my assigned tasks sorted by priority",
    description="Returns all PENDING and ACCEPTED tasks assigned to the currently authenticated volunteer.",
)
def my_tasks(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    tasks = (
        db.query(Task)
        .filter(
            Task.volunteer_id == current_user.id,
            Task.status.in_(["PENDING", "ACCEPTED"]),
        )
        .all()
    )
    # Sort in Python — CRITICAL first
    tasks.sort(key=lambda t: PRIORITY_ORDER.get(t.priority, 99))
    return tasks


@router.patch(
    "/tasks/{task_id}/accept",
    response_model=TaskOut,
    summary="Accept a dispatched task",
)
def accept_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.volunteer_id == current_user.id)
        .first()
    )
    if not task:
        raise NotFoundError("Task", task_id)
    if task.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot accept a task that is already {task.status}.",
        )

    task.status = "ACCEPTED"
    db.commit()
    db.refresh(task)
    logger.info(f"Task {task_id} ACCEPTED by volunteer {current_user.email}")
    return task


@router.patch(
    "/tasks/{task_id}/complete",
    response_model=TaskOut,
    summary="Mark a task as completed",
)
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.volunteer_id == current_user.id)
        .first()
    )
    if not task:
        raise NotFoundError("Task", task_id)
    if task.status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is already completed.",
        )

    task.status = "COMPLETED"
    task.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    logger.info(f"Task {task_id} COMPLETED by volunteer {current_user.email}")
    return task


@router.get(
    "/notifications",
    summary="Get my volunteer notifications",
)
def volunteer_notifications(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    notifications = (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(30)
        .all()
    )
    unread = [n for n in notifications if not n.read]

    return {
        "unread_count": len(unread),
        "notifications": [
            {
                "id": str(n.id),
                "title": n.title,
                "message": n.message,
                "read": n.read,
                "priority": n.priority,
                "type": n.type,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
    }
