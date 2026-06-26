from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: Optional[int] = None
    actor_email: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    created_at: datetime
    signature_algorithm: Optional[str] = None
    signature_valid: Optional[bool] = None

    class Config:
        from_attributes = True


class ActivityLogResponse(BaseModel):
    id: int
    event_type: str
    resource_type: str
    resource_id: int
    title: str
    description: Optional[str] = None
    actor_name: Optional[str] = None
    actor_email: Optional[str] = None
    status: str
    created_at: datetime
