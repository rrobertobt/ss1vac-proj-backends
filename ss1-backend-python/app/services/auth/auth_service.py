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
from fastapi import HTTPException

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
            extra={"email": user.email, "username": user.username, "role_id": user.role_id},
        )

    def public_user(self, user):
        # Extraer códigos de permisos del rol
        permissions = [p.code for p in user.role.permissions] if user.role and user.role.permissions else []

        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role_id": user.role_id,
            "role_name": user.role.name if user.role else None,
            "role_label": user.role.label if user.role else None,
            "two_fa_enabled": user.two_fa_enabled,
            "permissions": permissions,
            "employee": user.employee if user.employee else None,
            "patient": user.patient if user.patient else None,
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

    async def request_password_reset(self, email: str):
        """Solicita recuperación de contraseña - envía código al correo"""
        user = await self.users.find_by_email_or_username(email)
        # Por seguridad, no revelamos si el email existe o no
        if not user or not user.is_active:
            return

        code = _gen_6_digit_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        await self.users.patch_user(
            user.id,
            {
                "password_reset_token": hash_value(code),
                "password_reset_expires": expires_at,
            },
        )

        self.mail.send_text_email(
            to=user.email,
            subject="Código de recuperación de contraseña",
            text=f"Tu código de recuperación es: {code}\n\nEste código expira en 15 minutos.",
        )

    async def reset_password(self, email: str, code: str, new_password: str):
        """Resetea la contraseña usando el código enviado"""
        user = await self.users.find_by_email_or_username(email)
        if not user or not user.is_active:
            return {"ok": False, "reason": "Usuario inválido"}

        if not user.password_reset_token or not user.password_reset_expires:
            return {"ok": False, "reason": "Código no solicitado"}

        if datetime.now(timezone.utc) > user.password_reset_expires:
            return {"ok": False, "reason": "Código expirado"}

        if not verify_hash(code, user.password_reset_token):
            return {"ok": False, "reason": "Código inválido"}

        # Hash de la nueva contraseña
        password_hash = hash_value(new_password)

        # Actualizar contraseña y limpiar token
        await self.users.patch_user(
            user.id,
            {
                "password_hash": password_hash,
                "password_reset_token": None,
                "password_reset_expires": None,
            },
        )

        return {"ok": True}

    async def change_password(self, user_id: int, current_password: str, new_password: str):
        """Cambia la contraseña de un usuario autenticado"""
        user = await self.users.find_by_id(user_id)
        if not user or not user.is_active:
            return {"ok": False, "reason": "Usuario inválido"}

        # Verificar que la contraseña actual sea correcta
        if not verify_hash(current_password, user.password_hash):
            return {"ok": False, "reason": "Contraseña actual incorrecta"}

        # Hash de la nueva contraseña
        password_hash = hash_value(new_password)

        # Actualizar contraseña
        await self.users.patch_user(
            user.id,
            {"password_hash": password_hash},
        )

        return {"ok": True}

    async def update_profile(self, user_id: int, profile_data: dict):
        """
        Actualiza el perfil del usuario autenticado.
        Puede actualizar username (users) y datos personales (patients).
        No permite actualizar nombres (first_name, last_name).
        """
        user = await self.users.find_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Usuario inválido")

        # Actualizar username si se proporciona
        if "username" in profile_data and profile_data["username"] is not None:
            # Verificar si el nuevo username ya existe
            existing_username = await self.users.find_by_username(profile_data["username"])
            if existing_username and existing_username.id != user_id:
                raise HTTPException(status_code=409, detail="El username ya está en uso")
            
            await self.users.patch_user(user_id, {"username": profile_data["username"]})

        # Si el usuario es paciente, actualizar datos del paciente
        if user.patient:
            patient_update = {}
            
            # Mapear campos de perfil a campos de paciente
            patient_fields = [
                "phone", "email", "address", "gender", "marital_status",
                "occupation", "education_level", "emergency_contact_name",
                "emergency_contact_relationship", "emergency_contact_phone"
            ]
            
            for field in patient_fields:
                if field in profile_data:
                    patient_update[field] = profile_data[field]
            
            # Si hay campos de paciente para actualizar
            if patient_update:
                from app.db.repositories.patients_repo import PatientsRepo
                patients_repo = PatientsRepo(self.users.db)
                await patients_repo.update(user.patient.id, patient_update)

        # Retornar el usuario actualizado
        return await self.users.find_by_id(user_id)
