"""Capability CRUD + search + recommend API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import Capability, CapUsageLog
from schemas import CapabilityCreate, CapabilityUpdate, CapabilityOut, FeedbackCreate
from response import ok, fail

router = APIRouter(prefix="/api/capabilities", tags=["能力管理"])


@router.get("")
async def list_capabilities(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: str = None, q: str = None, db: AsyncSession = Depends(get_db),
):
    query = select(Capability)
    count_query = select(func.count(Capability.id))
    if status:
        query = query.where(Capability.status == status)
        count_query = count_query.where(Capability.status == status)
    if q:
        like = f"%{q}%"
        query = query.where(or_(Capability.name.ilike(like), Capability.description.ilike(like)))
        count_query = count_query.where(or_(Capability.name.ilike(like), Capability.description.ilike(like)))
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Capability.usage_count.desc()).offset((page-1)*page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()
    return ok({"items": [CapabilityOut.model_validate(c).model_dump() for c in items], "total": total})


@router.get("/search")
async def search_capabilities(q: str = Query(...), limit: int = Query(10, ge=1), db: AsyncSession = Depends(get_db)):
    like = f"%{q}%"
    result = await db.execute(
        select(Capability).where(
            Capability.status == "published",
            or_(Capability.name.ilike(like), Capability.description.ilike(like)),
        ).order_by(Capability.usage_count.desc()).limit(limit)
    )
    items = [CapabilityOut.model_validate(c).model_dump() for c in result.scalars().all()]
    return ok(items)


@router.get("/drafts")
async def list_drafts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Capability).where(Capability.status == "draft").order_by(Capability.created_at.desc())
    )
    items = [CapabilityOut.model_validate(c).model_dump() for c in result.scalars().all()]
    return ok(items)


@router.get("/{cap_id}")
async def get_capability(cap_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Capability).where(Capability.id == cap_id))
    c = result.scalar_one_or_none()
    if not c:
        return fail(404, "能力不存在")
    return ok(CapabilityOut.model_validate(c).model_dump())


@router.post("", status_code=201)
async def create_capability(req: CapabilityCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(select(Capability).where(Capability.cap_id == req.cap_id))
    if exists.scalar_one_or_none():
        return fail(409, f"能力编号 {req.cap_id} 已存在")
    c = Capability(**req.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return ok(CapabilityOut.model_validate(c).model_dump(), msg="能力已创建")


@router.put("/{cap_id}")
async def update_capability(cap_id: str, req: CapabilityUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Capability).where(Capability.id == cap_id))
    c = result.scalar_one_or_none()
    if not c:
        return fail(404, "能力不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    c.version += 1
    await db.commit()
    await db.refresh(c)
    return ok(CapabilityOut.model_validate(c).model_dump(), msg="已更新")


@router.post("/{cap_id}/feedback")
async def record_feedback(cap_id: str, req: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Capability).where(Capability.id == cap_id))
    c = result.scalar_one_or_none()
    if not c:
        return fail(404, "能力不存在")
    log = CapUsageLog(capability_id=cap_id, project_id=req.project_id, context=req.context, feedback=req.feedback)
    db.add(log)
    if req.feedback == "useful":
        c.usage_count = (c.usage_count or 0) + 1
    await db.commit()
    return ok(msg="反馈已记录")


@router.post("/{cap_id}/publish")
async def publish_capability(cap_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Capability).where(Capability.id == cap_id))
    c = result.scalar_one_or_none()
    if not c:
        return fail(404, "能力不存在")
    c.status = "published"
    await db.commit()
    return ok(msg="能力已发布")
