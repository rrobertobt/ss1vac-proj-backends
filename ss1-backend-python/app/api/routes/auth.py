from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories.users_repo import UsersRepo
from app.services.mail_mailtrap import MailService
from app.services.auth.auth_service import AuthService
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginBody(BaseModel):
    emailOrUsername: str
    password: str

class TwoFaVerifyBody(BaseModel):
    challengeId: str
    code: str = Field(min_length=6, max_length=6)

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.post("/login")
async def login(body: LoginBody, db: AsyncSession = Depends(get_db)):
    users = UsersRepo(db)
    auth = AuthService(users, MailService())

    user = await auth.authenticate_user(body.emailOrUsername, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not user.two_fa_enabled:
        token = await auth.issue_access_token(user)
        await auth.update_last_login(user.id)
        return {"accessToken": token, "user": auth.public_user(user)}

    challenge_id = await auth.start_twofa(user.id, "login")
    return {"twoFaRequired": True, "challengeId": challenge_id}

@router.post("/2fa/verify")
async def verify_twofa(body: TwoFaVerifyBody, db: AsyncSession = Depends(get_db)):
    users = UsersRepo(db)
    auth = AuthService(users, MailService())

    result = await auth.verify_twofa_login(body.challengeId, body.code)
    if not result["ok"]:
        raise HTTPException(status_code=401, detail=result["reason"])

    user = result["user"]
    token = await auth.issue_access_token(user)
    await auth.update_last_login(user.id)
    return {"accessToken": token, "user": auth.public_user(user)}

@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    # current_user es un User SQLAlchemy
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "roleId": current_user.role_id,
            "roleName": current_user.role.name if current_user.role else None,
            "twoFaEnabled": current_user.two_fa_enabled,
        }
    }

@router.post("/2fa/enable/request")
async def request_enable_2fa(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    users = UsersRepo(db)
    auth = AuthService(users, MailService())

    challenge_id = await auth.start_twofa(current_user.id, "enable")
    return {"challengeId": challenge_id}

@router.post("/2fa/enable/confirm")
async def confirm_enable_2fa(body: TwoFaVerifyBody, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    users = UsersRepo(db)
    auth = AuthService(users, MailService())

    result = await auth.confirm_twofa_toggle(current_user.id, body.challengeId, body.code, "enable")
    if not result["ok"]:
        raise HTTPException(status_code=401, detail=result["reason"])
    return {"twoFaEnabled": True}

@router.post("/2fa/disable/request")
async def request_disable_2fa(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    users = UsersRepo(db)
    auth = AuthService(users, MailService())

    challenge_id = await auth.start_twofa(current_user.id, "disable")
    return {"challengeId": challenge_id}

@router.post("/2fa/disable/confirm")
async def confirm_disable_2fa(body: TwoFaVerifyBody, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    users = UsersRepo(db)
    auth = AuthService(users, MailService())

    result = await auth.confirm_twofa_toggle(current_user.id, body.challengeId, body.code, "disable")
    if not result["ok"]:
        raise HTTPException(status_code=401, detail=result["reason"])
    return {"twoFaEnabled": False}
