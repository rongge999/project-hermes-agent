"""Project CRUD API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import Project
from schemas import ProjectCreate, ProjectUpdate, ProjectOut
from response import ok, fail

router = APIRouter(prefix="/api/projects", tags=["项目管理"])


@router.get("")
async def list_projects(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: str = None, db: AsyncSession = Depends(get_db),
):
    query = select(Project)
    count_query = select(func.count(Project.id))
    if status:
        query = query.where(Project.status == status)
        count_query = count_query.where(Project.status == status)
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Project.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()
    return ok({"items": [ProjectOut.model_validate(p).model_dump() for p in items], "total": total, "page": page, "page_size": page_size})


@router.get("/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        return fail(404, "项目不存在")
    return ok(ProjectOut.model_validate(p).model_dump())


@router.post("", status_code=201)
async def create_project(req: ProjectCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(select(Project).where(Project.topic_id == req.topic_id))
    if exists.scalar_one_or_none():
        return fail(409, f"话题编号 {req.topic_id} 已存在")
    p = Project(**req.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return ok(ProjectOut.model_validate(p).model_dump(), msg="项目已创建")


@router.put("/{project_id}")
async def update_project(project_id: str, req: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        return fail(404, "项目不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return ok(ProjectOut.model_validate(p).model_dump(), msg="已更新")


@router.post("/{project_id}/archive")
async def archive_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        return fail(404, "项目不存在")
    p.status = "archived"
    await db.commit()
    return ok(msg="项目已归档")
