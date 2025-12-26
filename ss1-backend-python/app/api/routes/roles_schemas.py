from pydantic import BaseModel
from typing import Optional


class RoleResponse(BaseModel):
    id: int
    name: str
    label: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True
