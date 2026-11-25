from fastapi import APIRouter
from sqlalchemy.orm import Session

from database import get_db
from exceptions.bot_exceptions import BotNotFoundError, BotRunningError

from schemas.bot_schema import BotCreateSchema, BotCreateResponseSchema
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, Request, Depends, status

router = APIRouter(tags=["bots"])
from repositories.bot_repository import BotRepository
from botpackage.manager.bot_manager import BotManager


def get_bot_manager(request: Request) -> BotManager:
    return request.app.state.bot_manager


# @router.get("/api/v1/debug/bots")
# async def get_debug_bot_states(db: Session = Depends(get_db)):
#     repo = BotRepository(db)
#     bot_debug_data = {}
#
#     for symbol, bot in manager.active_bots.items():
#         bot_debug_data[symbol] = {
#             "running": bot.running,
#             "stream_url": bot.stream_url,
#             "cached_alerts_count": len(bot.cached_alerts),
#             # "cached_alerts": [
#             #     {
#             #         "id": a["id"],
#             #         "alarm_type": str(a["alarm_type"]),
#             #         "direction": str(a["direction"]),
#             #         "target_price": a["target_price"],
#             #         "target_percentage": a["target_percentage"],
#             #         "user_id": a["user_id"]
#             #     } for a in bot.cached_alerts
#             # ]
#         }
#
#     return {
#         "total_active_bots": len(manager.active_bots),
#         "bots": bot_debug_data
#     }


@router.post("/createbot", response_model=BotCreateResponseSchema)
async def createBot(payload: BotCreateSchema, db: Session = Depends(get_db)):
    repo = BotRepository(db)
    try:
        bot = repo.create_bot(payload.symbol)
        return {
            "id": bot.id,
            "symbol": bot.symbol,
            "status": "success",
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Datenbankfehler beim Anlegen des Bots.",
        )


@router.get("/bots")
async def get_bots(db: Session = Depends(get_db)):
    repo = BotRepository(db)

    try:
        bots = repo.get_all()
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


@router.get("/active-bots")
async def get_all_active_bots(db: Session = Depends(get_db)):
    repo = BotRepository(db)
    try:
        bots = repo.get_active()
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


@router.delete("/delete/{symbol}")
async def delete_bot(symbol: str, db: Session = Depends(get_db)):
    repo = BotRepository(db)

    try:
        deleted_bot = repo.delete_bot(symbol)
        return {
            "status": "ok",
            "msg": f"Bot für {deleted_bot.symbol} wurde gelöscht.",
        }
    except BotNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except BotRunningError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Datenbankfehler beim Löschen des Bots.",
        )


@router.post("/start/{bot_id}")
async def start_bot(bot_id: int, manager: BotManager = Depends(get_bot_manager)):
    return await manager.start_bot(bot_id)


@router.post("/stopp/{bot_id}")
async def stopp_bot(bot_id: int, manager: BotManager = Depends(get_bot_manager)):
    try:
        return await manager.stop_bot(bot_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
