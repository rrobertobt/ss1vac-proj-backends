from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.db.repositories.users_repo import UsersRepo

bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="No autenticado")

    payload = decode_token(creds.credentials, settings.JWT_ACCESS_SECRET)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    users = UsersRepo(db)
    user = await users.find_by_id(int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Token inválido")

    return user
