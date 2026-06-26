import json
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.utils.audit_signature import AUDIT_SIGNATURE_ALGORITHM, sign_audit_log


class AuditLogService:
    @staticmethod
    def create(
        db: Session,
        action: str,
        actor: Optional[User] = None,
        actor_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        detail: Optional[Any] = None,
        request: Optional[Request] = None,
        success: bool = True,
    ) -> AuditLog:
        if isinstance(detail, (dict, list)):
            detail_value = json.dumps(detail, ensure_ascii=True, default=str)
        elif detail is None:
            detail_value = None
        else:
            detail_value = str(detail)

        log = AuditLog(
            actor_user_id=actor.id if actor else None,
            actor_email=actor.email if actor else actor_email,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            detail=detail_value,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            success=success,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        signature = sign_audit_log(log)
        if signature:
            log.signature_algorithm = AUDIT_SIGNATURE_ALGORITHM
            log.signature = signature

        db.add(log)
        return log
