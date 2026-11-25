from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from database import get_db
from utils.limiter import limiter
from serverpackage.utils.utils import FindUser
from schemas.user_schemas import CreateUserSchema, UserLoginSchema
from sqlalchemy.orm import Session
from models.user_model import User
from serverpackage.utils.security import hash_password, verify_pw, create_access_token, create_refresh_token, decode_jwt

router = APIRouter(tags=["auth"])


@router.post("/register")
@limiter.limit("5/minute")
def register_user(request: Request, user_data: CreateUserSchema, response: Response, db: Session = Depends(get_db)):
    # test if email already exists
    if FindUser(str(user_data.email), db):
        raise HTTPException(status_code=400, detail="Email existiert")

    password = hash_password(user_data.password)

    new_user = User(
        email=user_data.email,
        hashedPassword=password,
        # is_admin=False
    )

    db.add(new_user)
    db.commit()

    token_data = {"sub": str(new_user.id),
                  "is_admin": new_user.isAdmin}  # 💡 Tipp: Nutze lieber user.id statt der E-Mail für 'sub'
    token = create_access_token(token_data)

    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=1800,
        samesite="lax",
        secure=False
    )
    return {"message": "User erfolgreich registriert"}


ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


@limiter.limit("5/minute")
@router.post("/login")
def login_user(request: Request, login_data: UserLoginSchema, response: Response, db: Session = Depends(get_db)):
    user = FindUser(str(login_data.email), db)

    # ⚠️ Kleiner Logik-Fix: Erst das Passwort prüfen, DANACH das Token generieren!
    if not user or not verify_pw(login_data.password, user.hashedPassword):
        raise HTTPException(status_code=401, detail="Email or Password incorrect.")

    token_data = {"sub": str(user.id),
                  "is_admin": user.isAdmin}  # 💡 Tipp: Nutze lieber user.id statt der E-Mail für 'sub'
    access_token = create_access_token(token_data, expires_delta=timedelta(minutes=15))
    refresh_token = create_refresh_token(token_data, expires_delta=timedelta(days=7))

    # 2. Access Token Cookie setzen (15 Minuten)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=15 * 60  # 15 Minuten in Sekunden
    )

    # 3. Refresh Token Cookie setzen (7 Tage, beschränkt auf Refresh-Route)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/api/auth/refresh",  # Cookie wird NUR an diesen Endpunkt gesendet!
        max_age=7 * 24 * 60 * 60  # 7 Tage in Sekunden
    )

    return {"status": "Erfolgreich eingeloggt", "is_admin": user.isAdmin}


@router.post("/api/auth/refresh")
def refresh_token(request: Request, response: Response):
    # 1. Refresh-Token aus Cookie lesen
    re_token = request.cookies.get("refresh_token")
    if not re_token:
        raise HTTPException(status_code=401, detail="Kein Refresh-Token vorhanden")

    try:
        # 2. Refresh-Token validieren
        payload = decode_jwt(re_token)

        # Sicherstellen, dass es wirklich ein Refresh-Token ist
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Ungültiger Token-Typ")

        user_id = payload.get("sub")
        is_admin = payload.get("is_admin", False)

        if not user_id:
            raise HTTPException(status_code=401, detail="Ungültiger Token-Payload")

        # 3. Frisches Access-Token (15 Min) generieren
        new_access_token = create_access_token(
            data={"sub": str(user_id), "is_admin": is_admin},
            expires_delta=timedelta(minutes=15)
        )

        # 4. Neues Access-Token-Cookie setzen
        response.set_cookie(
            key="access_token",
            value=f"Bearer {new_access_token}",
            httponly=True,
            secure=False,  # ✅ Einheitlich auf IS_PRODUCTION gesetzt
            samesite="lax",
            max_age=15 * 60
        )

        return {"status": "refreshed"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Ungültiges oder abgelaufenes Refresh-Token")


@router.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")
    return {"status": "logged_out"}
