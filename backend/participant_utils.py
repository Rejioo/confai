from sqlalchemy.orm import Session
from models import User

def extract_participants_from_text(message: str, db: Session):
    msg = message.lower()
    found = []

    users = db.query(User).all()

    for user in users:
        name = user.name.lower()
        if name in msg:
            found.append(user.name)

    return found
