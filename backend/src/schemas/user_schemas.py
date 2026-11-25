import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class CreateUserSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, value: str) -> str:
        if not re.search(r"[a-z]", value):
            raise ValueError("Das Passwort muss mindestens einen Kleinbuchstaben enthalten.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Das Passwort muss mindestens einen Großbuchstaben enthalten.")
        if not re.search(r"[0-9]", value):
            raise ValueError("Das Passwort muss mindestens eine Zahl enthalten.")
        if not re.search(r"[^a-zA-Z0-9]", value):
            raise ValueError(
                "Das Passwort muss mindestens ein Sonderzeichen enthalten (z. B. !, $, %, @)."
            )
        return value


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str
