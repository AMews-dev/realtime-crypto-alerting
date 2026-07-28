from enum import verify
import jwt
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, status, Response, APIRouter, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from limits.strategies import RateLimiter
from sqlalchemy import Null
from sqlalchemy.orm import Session
from botpackage.manager import BotManager
from serverpackage.utils.security import hash_password, verify_pw, create_access_token, get_current_admin, \
    get_current_user
from serverpackage.utils.utils import FindUser
from shared.schemas import CreateUser, UserLogin, BotCreateSchema, BotCreateResponseSchema, StopBotSchema, \
    CreateAlertSchema, CreateAlertResponseSchema
from contextlib import asynccontextmanager
import sys
from database import check_db_connection, Base, engine, get_db, SessionLocal
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
# import for db
from shared.price_alarm_model import PriceAlarm
from shared.coin_model import CryptoCoin
from shared.bot_model import BotModel
from shared.user_model import User
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import asyncio

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
    "http://localhost:8000"
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


@app.post("/create-alert", response_model=CreateAlertResponseSchema)
def create_alert(payload: CreateAlertSchema, db: Session = Depends(get_db),
                 current_user_payload: dict = Depends(get_current_user)):
    # first validate payload

    #validate current user -> get user id check if user exists in db
    user_id = int(current_user_payload.get("sub"))
    aktueller_preis = 100.0  # Platzhalter für deine Live-Preis-Logik

    berechneter_target_price = payload.target_price
    berechnete_direction = payload.direction.upper() if payload.direction else "UP"

    # Logik für Prozent-Alarm
    if payload.target_percentage is not None:
        berechneter_target_price = aktueller_preis * (1 + (payload.target_percentage / 100))
        berechnete_direction = "UP" if payload.target_percentage > 0 else "DOWN"

    # Logik für festen Preis-Alarm (Richtung validieren)
    elif payload.target_price is not None:
        berechnete_direction = "UP" if payload.target_price > aktueller_preis else "DOWN"

    alert = PriceAlarm(
        user_id=user_id,
        coin_symbol=payload.coin_symbol,
        activation_price=1000,
        is_active=payload.is_active,
        target_percentage=berechneter_target_price,
        target_price=payload.target_price,
        direction=berechnete_direction,
        is_triggered=False
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@app.post("/register")
@limiter.limit("5/minute")
def register_user(request: Request, user_data: CreateUser, db: Session = Depends(get_db)):
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
    return {"message": "User erfolgreich registriert"}


@limiter.limit("5/minute")
@app.post("/login")
def login_user(request: Request,login_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = FindUser(login_data.email, db)

    # ⚠️ Kleiner Logik-Fix: Erst das Passwort prüfen, DANACH das Token generieren!
    if not user or not verify_pw(login_data.password, user.hashedPassword):
        raise HTTPException(status_code=401, detail="Email or Password incorrect.")

    token_data = {"sub": str(user.id), "is_admin": user.isAdmin} # 💡 Tipp: Nutze lieber user.id statt der E-Mail für 'sub'
    token = create_access_token(token_data)

    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=1800,
        samesite="lax",
        secure=False
    )

    return {"status": "Erfolgreich eingeloggt", "is_admin": user.isAdmin}


if __name__ == '__main__':
    from botpackage.manager import BotManager

    print(BotManager)
    uvicorn.run(app, host="localhost", port=8000)
