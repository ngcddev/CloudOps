# Contraseñas con hash y tokens de sesión (spec 007, T03).
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings
from app.models.user import User

ALGORITHM = "HS256"
TOKEN_MINUTES = 60


class InvalidToken(Exception):
    """El token falta, está mal formado, venció o fue firmado con otra clave."""


def hash_password(password: str) -> str:
    """Devuelve el hash bcrypt de la contraseña (nunca se guarda en claro)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode("ascii")


def verify_password(password: str, password_hash: str | None) -> bool:
    """Compara la contraseña con su hash; sin hash (usuario sin contraseña) siempre es falso."""
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        return False


def create_token(user: User, now: datetime | None = None) -> str:
    """Crea el token de 60 minutos con el id, el rol y el cliente del usuario."""
    issued = now or datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "client_id": user.client_id,
        "iat": issued,
        "exp": issued + timedelta(minutes=TOKEN_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Valida firma y vencimiento; lanza InvalidToken si algo falla."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError as error:
        raise InvalidToken(str(error)) from error
