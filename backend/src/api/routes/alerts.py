from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db

from serverpackage.utils.security import get_current_user
from models.price_alarm_model import PriceAlarm
from schemas.price_alert_schema import CreateAlertSchema, AlertResponseSchema
router = APIRouter(tags=["alerts"])

@router.post("/create-alert", response_model=AlertResponseSchema)
def create_alert(payload: CreateAlertSchema, db: Session = Depends(get_db),
                 current_user_payload: dict = Depends(get_current_user)):
    # first validate payload

    #validate current user -> get user id check if user exists in db
    user_id = int(current_user_payload.get("sub"))

    new_alert = PriceAlarm(**payload.model_dump(), user_id=user_id)
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    return new_alert


@router.get("/api/alerts", response_model=list[AlertResponseSchema])
def get_user_alerts(db: Session = Depends(get_db),
                    current_user_payload: dict = Depends(get_current_user)):
    user_id = int(current_user_payload.get("sub"))

    user_alerts = db.query(PriceAlarm).filter(PriceAlarm.user_id == user_id).all()
    return user_alerts