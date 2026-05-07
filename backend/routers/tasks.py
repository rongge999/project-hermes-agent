"""Task management API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from database import get_db
from models import Task
from schemas import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskOut
from response import ok, fail

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


@router.get("")
async def list_tasks(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    project_id: str = None, status: str = None, priority: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Task)
    count_query = select(func.count(Task.id))
    if project_id:
        query = query.where(Task.project_id == project_id)
        count_query = count_query.where(Task.project_id == project_id)
    if status:
        query = query.where(Task.status == status)
        count_query = count_query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
        count_query = count_query.where(Task.priority == priority)
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Task.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()
    return ok({"items": [TaskOut.model_validate(t).model_dump() for t in items], "total": total})


@router.get("/{task_id}")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    t = result.scalar_one_or_none()
    if not t:
        return fail(404, "任务不存在")
    return ok(TaskOut.model_validate(t).model_dump())


@router.post("", status_code=201)
async def create_task(req: TaskCreate, db: AsyncSession = Depends(get_db)):
    t = Task(**req.model_dump())
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return ok(TaskOut.model_validate(t).model_dump(), msg="任务已创建")


@router.put("/{task_id}")
async def update_task(task_id: str, req: TaskUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    t = result.scalar_one_or_none()
    if not t:
        return fail(404, "任务不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    await db.commit()
    await db.refresh(t)
    return ok(TaskOut.model_validate(t).model_dump())


@router.put("/{task_id}/status")
async def update_task_status(task_id: str, req: TaskStatusUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    t = result.scalar_one_or_none()
    if not t:
        return fail(404, "任务不存在")
    t.status = req.status
    if req.status == "done":
        t.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(t)
    return ok(TaskOut.model_validate(t).model_dump())
