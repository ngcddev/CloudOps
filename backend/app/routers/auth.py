# Endpoints de sesión: iniciar sesión y consultar el usuario actual (spec 007, T04).
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models.user import User
from app.schemas.auth import LoginIn, TokenOut, UserOut
from app.services.auth import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Hash de relleno: si el correo no existe se verifica igual, para que el tiempo no delate qué correos existen
_DUMMY_HASH = hash_password("relleno-para-igualar-tiempos")
_BAD_LOGIN = "Correo o contraseña incorrectos."


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    """Valida correo y contraseña y devuelve el token de sesión."""
    email = data.email.strip().lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    valid = verify_password(data.password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not valid or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_BAD_LOGIN)

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return TokenOut(access_token=create_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    """Devuelve quién es el usuario de la sesión, su rol y su cliente."""
    return user
