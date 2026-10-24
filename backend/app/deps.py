# Dependencias de FastAPI para la sesión y los permisos: usuario actual, rol y alcance por cliente (spec 007, T05).
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.services.auth import InvalidToken, decode_token

# auto_error=False: la respuesta 401 la armamos nosotros, en español
_bearer = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Devuelve el usuario de la sesión; 401 si falta el token, venció o el usuario está inactivo."""
    if credentials is None:
        raise _unauthorized("Debes iniciar sesión.")
    try:
        claims = decode_token(credentials.credentials)
        user_id = int(claims["sub"])
    except (InvalidToken, ValueError):
        raise _unauthorized("Tu sesión no es válida o venció. Vuelve a iniciar sesión.") from None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Tu sesión no es válida o venció. Vuelve a iniciar sesión.")
    return user


def require_role(role: str) -> Callable[..., User]:
    """Dependencia que deja pasar solo al rol indicado (403 para los demás)."""

    def checker(user: User = Depends(current_user)) -> User:
        if user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para esta acción.")
        return user

    return checker


require_agency = require_role("agencia")


def client_scope(user: User) -> int | None:
    """`None` si el usuario ve todo (agencia); si no, el id del único cliente que puede ver."""
    if user.role == "agencia":
        return None
    if user.client_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tu usuario no tiene un cliente asignado.")
    return user.client_id
