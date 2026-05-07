"""SQLAlchemy models for Hermes Agent."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Integer, BigInteger, DateTime, ForeignKey, JSON
from database import Base


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, default=_uuid)
    topic_id = Column(String(10), unique=True, nullable=False, comment="话题编号 #001")
    name = Column(String(200), nullable=False)
    description = Column(Text)
    tech_stack = Column(JSON)
    repo_path = Column(String(500))
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(String(36), primary_key=True, default=_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    source = Column(String(50), default="manual")
    status = Column(String(20), default="todo")
    priority = Column(String(10), default="P2")
    feishu_record_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=_now)
    completed_at = Column(DateTime(timezone=True))


class Capability(Base):
    __tablename__ = "capabilities"
    id = Column(String(36), primary_key=True, default=_uuid)
    cap_id = Column(String(20), unique=True, nullable=False, comment="CAP-001")
    name = Column(String(200), nullable=False)
    description = Column(Text)
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    call_type = Column(String(20), nullable=False)
    call_definition = Column(Text)
    source_project_id = Column(String(36), ForeignKey("projects.id"))
    feishu_record_id = Column(String(100))
    status = Column(String(20), default="draft")
    version = Column(Integer, default=1)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)


class CapVersion(Base):
    __tablename__ = "cap_versions"
    id = Column(String(36), primary_key=True, default=_uuid)
    capability_id = Column(String(36), ForeignKey("capabilities.id"), nullable=False)
    version = Column(Integer, nullable=False)
    change_log = Column(Text)
    snapshot = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=_now)


class CapUsageLog(Base):
    __tablename__ = "cap_usage_logs"
    id = Column(String(36), primary_key=True, default=_uuid)
    capability_id = Column(String(36), ForeignKey("capabilities.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"))
    context = Column(String(200))
    feedback = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=_now)


class DocLink(Base):
    __tablename__ = "doc_links"
    id = Column(String(36), primary_key=True, default=_uuid)
    feishu_doc_token = Column(String(100), nullable=False)
    feishu_doc_title = Column(String(300))
    linked_type = Column(String(20), nullable=False)
    linked_id = Column(String(100))
    linked_url = Column(String(500))
    last_checked_at = Column(DateTime(timezone=True))
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    before_snapshot = Column(JSON)
    after_snapshot = Column(JSON)
    performed_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=_now)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    event_type = Column(String(50))
    raw_payload = Column(JSON)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=_now)
