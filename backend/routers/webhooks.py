"""Git Webhook receiver."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import WebhookEvent
from response import ok

router = APIRouter(prefix="/api/webhooks", tags=["Webhook"])


@router.post("/git")
async def git_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    event_type = request.headers.get("X-GitHub-Event", request.headers.get("X-Gitlab-Event", "push"))
    source = "github" if "X-GitHub-Event" in request.headers else "gitlab" if "X-Gitlab-Event" in request.headers else "unknown"
    event = WebhookEvent(source=source, event_type=event_type, raw_payload=body)
    db.add(event)
    await db.commit()
    return ok(msg="事件已接收")
