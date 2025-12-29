from pydantic import BaseModel, Field
from typing import Optional


class RoleResponse(BaseModel):
    id: int
    name: str
    label: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    id: int
    code: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class RolePermissionsResponse(BaseModel):
    role: RoleResponse
    permissions: list[PermissionResponse]


class UpdateRolePermissionsRequest(BaseModel):
    permission_ids: list[int] = Field(
        ..., min_length=0, description="Lista de IDs de permisos a asignar al rol"
    )

