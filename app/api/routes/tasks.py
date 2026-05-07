import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_session
from app.core.security import require_auth
from app.models.tasks import Task, VALID_STAGES, VALID_PRIORITIES
from app.core.config import settings

logger = logging.getLogger("itwin_ops.tasks")
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def _next_task_id(session: AsyncSession) -> str:
    result = await session.execute(select(Task.id))
    existing = result.scalars().all()
    nums = [int(tid.replace("T-", "")) for tid in existing if tid.startswith("T-") and tid[2:].isdigit()]
    return f"T-{str((max(nums) + 1) if nums else 1).zfill(3)}"


@router.get("/tasks-pipeline", response_class=HTMLResponse, tags=["Tasks"])
async def tasks_pipeline_page(request: Request, user: dict = Depends(require_auth)):
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "user": user,
        "app_name": settings.APP_NAME,
        "stages": VALID_STAGES,
    })


@router.get("/api/tasks", tags=["Tasks"])
async def list_tasks(
    request: Request,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
    stage: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    q = select(Task).order_by(Task.created_at.desc())
    if stage and stage in VALID_STAGES:
        q = q.where(Task.stage == stage)
    if priority and priority in VALID_PRIORITIES:
        q = q.where(Task.priority == priority)
    result = await session.execute(q)
    tasks = result.scalars().all()
    if search:
        s = search.lower()
        tasks = [t for t in tasks if s in t.title.lower() or s in (t.desc or "").lower()]
    return {"total": len(tasks), "tasks": [t.to_dict() for t in tasks]}


@router.get("/api/tasks/pipeline-stats", tags=["Tasks"])
async def pipeline_stats(
    request: Request,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Task.stage))
    stages_raw = result.scalars().all()
    counts = {s: 0 for s in VALID_STAGES}
    for s in stages_raw:
        if s in counts:
            counts[s] += 1
    total = len(stages_raw)
    complete = counts.get("complete", 0)
    return {
        "stage_counts": counts,
        "total": total,
        "complete": complete,
        "completion_pct": round(complete / total * 100) if total else 0,
    }


@router.get("/api/tasks/{task_id}", tags=["Tasks"])
async def get_task(
    task_id: str,
    request: Request,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.post("/api/tasks", tags=["Tasks"])
async def create_task(
    request: Request,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    body = await request.json()
    if not body.get("title"):
        raise HTTPException(status_code=422, detail="title is required")
    stage = body.get("stage", "registration")
    if stage not in VALID_STAGES:
        stage = "registration"
    priority = body.get("priority", "Medium")
    if priority not in VALID_PRIORITIES:
        priority = "Medium"
    task_id = await _next_task_id(session)
    task = Task(
        id=task_id,
        title=body["title"].strip(),
        desc=body.get("desc", ""),
        stage=stage,
        priority=priority,
        tags=json.dumps(body.get("tags", [])),
        assignee=body.get("assignee", ""),
        comments=json.dumps([]),
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    logger.info(f"Task created: {task_id} by {user.get('sub')}")
    return task.to_dict()


@router.patch("/api/tasks/{task_id}/stage", tags=["Tasks"])
async def advance_task_stage(
    task_id: str,
    request: Request,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    body = await request.json()
    new_stage = body.get("stage")
    if not new_stage or new_stage not in VALID_STAGES:
        raise HTTPException(status_code=422, detail=f"stage must be one of {VALID_STAGES}")
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.stage = new_stage
    task.updated_at = datetime.utcnow()
    session.add(task)
    await session.commit()
    return task.to_dict()


@router.patch("/api/tasks/{task_id}", tags=["Tasks"])
async def update_task(
    task_id: str,
    request: Request,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    body = await request.json()
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if "title" in body and body["title"].strip():
        task.title = body["title"].strip()
    if "desc" in body:
        task.desc = body["desc"]
    if "priority" in body and body["priority"] in VALID_PRIORITIES:
        task.priority = body["priority"]
    if "stage" in body and body["stage"] in VALID_STAGES:
        task.stage = body["stage"]
    if "tags" in body and isinstance(body["tags"], list):
        task.tags = json.dumps(body["tags"])
    if "assignee" in body:
        task.assignee = body["assignee"]
    task.updated_at = datetime.utcnow()
    session.add(task)
    await session.commit()
    return task.to_dict()


@router.post("/api/tasks/{task_id}/comments", tags=["Tasks"])
async def add_comment(
    task_id: str,
    request: Request,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    body = await request.json()
    text = body.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="comment text is required")
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    existing = task.comments_list()
    author = user.get("email", "user")
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    existing.append(f"[{ts}] {author}: {text}")
    task.comments = json.dumps(existing)
    task.updated_at = datetime.utcnow()
    session.add(task)
    await session.commit()
    return {"comments": existing}


@router.delete("/api/tasks/{task_id}", tags=["Tasks"])
async def delete_task(
    task_id: str,
    request: Request,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await session.delete(task)
    await session.commit()
    logger.info(f"Task deleted: {task_id} by {user.get('sub')}")
    return {"deleted": task_id}
