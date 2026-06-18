import email

from sqlalchemy.orm import Session

from shared.user_model import User

def FindUser(email: str, db: Session) -> User | None:
    return db.query(User).filter(User.email == email).first()