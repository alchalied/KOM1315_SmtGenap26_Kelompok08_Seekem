from pydantic import BaseModel
from typing import Optional

class ContactReporterRequest(BaseModel):
    whatsapp: str
    pesan: Optional[str] = None
