from http.client import HTTPException
from fastapi import Depends, HTTPException, status, Request
import bcrypt

from serverpackage.utils.utils import FindUser
from shared.user_model import User

from datetime import datetime, timedelta, timezone
import jwt


def hash_password(password: str) -> str:
    password_bytes = password.encode("UTF-8")

    salt = bcrypt.gensalt()

    hashed_bytes = bcrypt.hashpw(password_bytes, salt)

    return hashed_bytes.decode("UTF-8")


def verify_pw(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("UTF-8")
    hashed_password_bytes = hashed_password.encode("UTF-8")
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


SECRET_KEY = "SUPER_GEHEIMES_GEHEIMNIS_FUER_DEN_KRYPTO_BOT"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Wie lange das Token gültig ist


def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    # Ablaufzeitpunkt berechnen (Aktuelle Zeit + 30 Minuten)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Ablaufzeit ('exp') zum Token-Inhalt hinzufügen
    to_encode.update({"exp": expire})

    # Token mit dem SECRET_KEY verschlüsseln/signieren
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def get_current_user_token_payload(request: Request) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nicht autorisiert oder Sitzung abgelaufen.",
    )
    cookie_token = request.cookies.get("access_token")
    if not cookie_token or not cookie_token.startswith("Bearer "):
        raise credentials_exception

    token = cookie_token.split(" ")[1]

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("sub") is None:
            raise credentials_exception

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sitzung abgelaufen. Bitte neu einloggen.")
    except jwt.InvalidTokenError:
        raise credentials_exception


def get_current_admin(payload: dict = Depends(get_current_user_token_payload)) -> dict:
    if not payload.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Zugriff verweigert. Nur für Admins gestattet."
        )
    return payload
