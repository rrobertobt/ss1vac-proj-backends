from datetime import datetime, timedelta, timezone
from secrets import randbelow
from app.core.config import settings
from app.core.security import (
    verify_hash,
    hash_value,
    create_access_token,
    create_2fa_challenge,
    decode_2fa_challenge,
)
from app.db.repositories.users_repo import UsersRepo
MAX_2FA_ATTEMPTS = 5
TWOFA_TTL_MINUTES = 10

def _gen_6_digit_code() -> str:
    return str(randbelow(1_000_000)).zfill(6)

class AuthService:
    def __init__(self, users: UsersRepo, mail):
        self.users = users
        self.mail = mail

    async def authenticate_user(self, email_or_username: str, password: str):
        user = await self.users.find_by_email_or_username(email_or_username)
        if not user or not user.is_active:
            return None
        if not verify_hash(password, user.password_hash):
            return None
        return user

    async def issue_access_token(self, user) -> str:
        return create_access_token(
            subject=str(user.id),
            secret=settings.JWT_ACCESS_SECRET,
            expires_in=settings.JWT_ACCESS_EXPIRES_IN,
            extra={"email": user.email, "roleId": user.role_id},
        )

    def public_user(self, user):
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "roleId": user.role_id,
            "twoFaEnabled": user.two_fa_enabled,
        }

    async def update_last_login(self, user_id: int):
        await self.users.patch_user(user_id, {"last_login_at": datetime.now(timezone.utc)})

    async def _store_twofa_code(self, user_id: int, code: str):
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=TWOFA_TTL_MINUTES)
        await self.users.patch_user(
            user_id,
            {
                "two_fa_secret": hash_value(code),
                "two_fa_expires_at": expires_at,
                "two_fa_attempts": 0,
            },
        )

    async def _send_twofa_email(self, to: str, code: str, purpose: str):
        subject_map = {
            "login": "Tu código de verificación",
            "enable": "Código para activar 2FA",
            "disable": "Código para desactivar 2FA",
        }
        subject = subject_map.get(purpose, "Código de verificación")
        text = f"Tu código es: {code}\n\nEste código expira en pocos minutos."
        self.mail.send_text_email(to=to, subject=subject, text=text)

    async def start_twofa(self, user_id: int, purpose: str) -> str:
        user = await self.users.find_by_id(user_id)
        code = _gen_6_digit_code()
        await self._store_twofa_code(user_id, code)
        await self._send_twofa_email(user.email, code, purpose)

        return create_2fa_challenge(
            user_id=user_id,
            purpose=purpose,  # login/enable/disable
            secret=settings.JWT_2FA_SECRET,
            expires_in=settings.JWT_2FA_EXPIRES_IN,
        )

    async def verify_twofa_login(self, challenge_id: str, code: str):
        payload = decode_2fa_challenge(challenge_id, settings.JWT_2FA_SECRET)
        if not payload or payload.get("purpose") != "login":
            return {"ok": False, "reason": "Challenge inválido o expirado"}

        user_id = int(payload["sub"])
        user = await self.users.find_by_id(user_id)
        if not user or not user.is_active:
            return {"ok": False, "reason": "Usuario inválido"}

        if not user.two_fa_expires_at:
            return {"ok": False, "reason": "Código no solicitado"}
        if datetime.now(timezone.utc) > user.two_fa_expires_at:
            return {"ok": False, "reason": "Código expirado"}

        attempts = int(user.two_fa_attempts or 0)
        if attempts >= MAX_2FA_ATTEMPTS:
            return {"ok": False, "reason": "Demasiados intentos. Solicita un nuevo código."}

        if not verify_hash(code, user.two_fa_secret or ""):
            await self.users.patch_user(user.id, {"two_fa_attempts": attempts + 1})
            return {"ok": False, "reason": "Código inválido"}

        # consumir código
        await self.users.patch_user(
            user.id,
            {"two_fa_secret": None, "two_fa_expires_at": None, "two_fa_attempts": 0},
        )
        return {"ok": True, "user": user}

    async def confirm_twofa_toggle(self, user_id: int, challenge_id: str, code: str, action: str):
        payload = decode_2fa_challenge(challenge_id, settings.JWT_2FA_SECRET)
        if not payload or payload.get("purpose") != action:
            return {"ok": False, "reason": "Challenge inválido o expirado"}

        if int(payload["sub"]) != user_id:
            return {"ok": False, "reason": "Challenge no corresponde al usuario"}

        user = await self.users.find_by_id(user_id)
        if not user:
            return {"ok": False, "reason": "Usuario inválido"}

        if not user.two_fa_expires_at or datetime.now(timezone.utc) > user.two_fa_expires_at:
            return {"ok": False, "reason": "Código expirado"}

        attempts = int(user.two_fa_attempts or 0)
        if attempts >= MAX_2FA_ATTEMPTS:
            return {"ok": False, "reason": "Demasiados intentos. Solicita un nuevo código."}

        if not verify_hash(code, user.two_fa_secret or ""):
            await self.users.patch_user(user.id, {"two_fa_attempts": attempts + 1})
            return {"ok": False, "reason": "Código inválido"}

        # aplicar cambio + consumir código
        await self.users.patch_user(
            user.id,
            {
                "two_fa_enabled": (action == "enable"),
                "two_fa_secret": None,
                "two_fa_expires_at": None,
                "two_fa_attempts": 0,
            },
        )
        return {"ok": True}
