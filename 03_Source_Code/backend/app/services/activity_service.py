from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.user import User


class ActivityLogService:
    @staticmethod
    def create(
        db: Session,
        event_type: str,
        resource_type: str,
        resource_id: int,
        title: str,
        status: str,
        actor: Optional[User] = None,
        description: Optional[Any] = None,
    ) -> ActivityLog:
        log = ActivityLog(
            actor_user_id=actor.id if actor else None,
            actor_name=actor.name if actor else None,
            actor_email=actor.email if actor else None,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            title=title,
            description=str(description) if description is not None else None,
            status=status,
        )
        db.add(log)
        return log
