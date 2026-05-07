"""Audit log query API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import AuditLog
from response import ok

router = APIRouter(prefix="/api/audit-logs", tags=["审计日志"])


@router.get("")
async def list_logs(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    entity_type: str = None, action: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
        count_query = count_query.where(AuditLog.entity_type == entity_type)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(AuditLog.id.desc()).offset((page-1)*page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()
    return ok({"items": [{"id": str(log.id), "action": log.action, "entity_type": log.entity_type,
                          "entity_id": log.entity_id, "performed_by": log.performed_by,
                          "created_at": log.created_at.isoformat() if log.created_at else None}
                         for log in items], "total": total})
