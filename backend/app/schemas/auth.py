# Esquemas del inicio de sesión: lo que entra en POST /api/auth/login y lo que sale (spec 007, T04).
from pydantic import BaseModel, ConfigDict, Field


class LoginIn(BaseModel):
    email: str = Field(max_length=200)
    password: str = Field(max_length=200)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    client_id: int | None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
