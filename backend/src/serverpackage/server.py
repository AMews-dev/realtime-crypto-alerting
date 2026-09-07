import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, status, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from botpackage.manager import BotManager
from serverpackage.utils.security import hash_password, verify_pw, create_access_token, get_current_user, create_refresh_token, decode_jwt
from serverpackage.utils.utils import FindUser
from shared.allschemas import CreateUser, UserLogin, BotCreateSchema, BotCreateResponseSchema, StopBotSchema, \
    CreateAlertSchema
from contextlib import asynccontextmanager
import sys
from database import check_db_connection, Base, engine, get_db, SessionLocal
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
# import for db
from shared.models.price_alarm_model import PriceAlarm
from shared.schemas.price_alarm import AlertResponseSchema, CreateAlertSchema
from shared.bot_model import BotModel
from shared.user_model import User
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import asyncio
from datetime import timedelta

notification_queue = asyncio.Queue()
db = SessionLocal()
manager = BotManager(db_session=db, notification_queue=notification_queue)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Datenbank-Verbindung prüfen
    if not check_db_connection():
        print("🛑 Server-Start abgebrochen: Datenbank nicht erreichbar. Überprüfe deine DATABASE_URL!")
        sys.exit(1)  # Beendet das Python-Skript hart mit einem Fehlercode

    # Wenn die Verbindung steht, erstellen wir direkt die Tabellen (falls noch nicht da)
    Base.metadata.create_all(bind=engine)
    print("📁 Tabellen-Struktur überprüft/erstellt.")

    # restore active bots from db after server went offline

    try:
        await manager.restore_active_bots(db=db)
    except Exception as e:
        print(f"⚠️ Fehler bei der Bot-Wiederherstellung: {e}")
    finally:
        db.close()

    yield  # Ab hier läuft der Server ganz normal und nimmt App-Anfragen an

    print("🛑 Server wird heruntergefahren...")


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def test():
    return "Hello World"

@app.get("/api/v1/debug/bots")
async def get_debug_bot_states():
    bot_debug_data = {}

    for symbol, bot in manager.active_bots.items():
        bot_debug_data[symbol] = {
            "running": bot.running,
            "stream_url": bot.stream_url,
            "cached_alerts_count": len(bot.cached_alerts),
            "cached_alerts": [
                {
                    "id": a["id"],
                    "alarm_type": str(a["alarm_type"]),
                    "direction": str(a["direction"]),
                    "target_price": a["target_price"],
                    "target_percentage": a["target_percentage"],
                    "user_id": a["user_id"]
                } for a in bot.cached_alerts
            ]
        }

    return {
        "total_active_bots": len(manager.active_bots),
        "bots": bot_debug_data
    }

@app.post("/createbot", response_model=BotCreateResponseSchema)
async def createBot(payload: BotCreateSchema, db: Session = Depends(get_db)):
    try:
        bot = manager.create_bot(data_schema=payload, db=db)
        return {
            "symbol": bot.symbol,
            "status": "success",
            "id": bot.id
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Das Symbol {payload.symbol.upper()} existiert bereits!"
        )


@app.get("/bots")
async def get_bots(db: Session = Depends(get_db)):
    try:
        bots = manager.get_all_bots(db=db)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Datenbankfehler beim Abrufen der Bots."
        )
    if not bots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no bots in db."
        )

    return bots


@app.get("/active-bots")
async def get_all_active_bots(db: Session = Depends(get_db)):
    try:
        bots = manager.get_all__active_bots(db=db)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Datenbankfehler beim Abrufen der Bots."
        )
    if not bots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no bots are active now."
        )

    return bots


@app.post("/start/{bot_id}")
async def start_bot(bot_id: int, db: Session = Depends(get_db)):
    result = await manager.start_bot(bot_id, db=db)
    return result


def update_bot_status_in_db(symbol: str, db: Session):
    try:
        db.query(BotModel).filter(BotModel.symbol == symbol).update(
            {"is_running": False}, synchronize_session=False
        )
        db.commit()
        print(f"✅ DB-Status für {symbol} im Hintergrund auf False gesetzt.")
    except Exception as e:
        print(f"⚠️ Hintergrund-DB-Update fehlgeschlagen: {e}")


@app.post("/stopp")
async def stopp_bot(payload: StopBotSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    await manager.stop_bot(payload.symbol)
    background_tasks.add_task(update_bot_status_in_db, payload.symbol, db)
    return {"status": "ok", "msg": f"Bot {payload.symbol} wird gestoppt."}


@app.post("/create-alert", response_model=AlertResponseSchema)
def create_alert(payload: CreateAlertSchema, db: Session = Depends(get_db),
                 current_user_payload: dict = Depends(get_current_user)):
    # first validate payload

    #validate current user -> get user id check if user exists in db
    user_id = int(current_user_payload.get("sub"))

    new_alert = PriceAlarm(**payload.model_dump(), user_id= user_id)
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    return new_alert


@app.get("/api/alerts", response_model=list[AlertResponseSchema])
def get_user_alerts(db: Session = Depends(get_db),
                    current_user_payload: dict = Depends(get_current_user)):
    user_id = int(current_user_payload.get("sub"))

    user_alerts = db.query(PriceAlarm).filter(PriceAlarm.user_id == user_id).all()
    return user_alerts


@app.post("/register")
@limiter.limit("5/minute")
def register_user(request: Request, user_data: CreateUser, response: Response, db: Session = Depends(get_db)):
    # test if email already exists
    if FindUser(user_data.email, db):
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
@app.post("/login")
def login_user(request: Request, login_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = FindUser(login_data.email, db)

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

@app.post("/api/auth/refresh")
@app.post("/api/auth/refresh")
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

    except Exception:
        raise HTTPException(status_code=401, detail="Ungültiges oder abgelaufenes Refresh-Token")

@limiter.limit("5/minute")
@app.post("/login")
def login_user(request: Request, login_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = FindUser(login_data.email, db)

    # 1. Passwort prüfen
    if not user or not verify_pw(login_data.password, user.hashedPassword):
        raise HTTPException(status_code=401, detail="Email or Password incorrect.")

    token_data = {
        "sub": str(user.id),
        "is_admin": user.isAdmin
    }

    # 2. Tokens generieren
    access_token = create_access_token(token_data, expires_delta=timedelta(minutes=15))
    refresh_token = create_refresh_token(token_data, expires_delta=timedelta(days=7))

    # 3. Access Token Cookie (15 Minuten)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,              # ✅ Auf True korrigiert (Schutz vor XSS)
        samesite="lax",
        secure=False,        # ✅ Auf False für HTTP / Localhost korrigiert
        max_age=15 * 60
    )

    # 4. Refresh Token Cookie (7 Tage)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,        # ✅ Auf False für HTTP / Localhost korrigiert
        path="/api/auth/refresh",
        max_age=7 * 24 * 60 * 60
    )

    return {"status": "Erfolgreich eingeloggt", "is_admin": user.isAdmin}



@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")
    return {"status": "logged_out"}


if __name__ == '__main__':
    from botpackage.manager import BotManager

    print(BotManager)
    uvicorn.run(app, host="localhost", port=8000)
