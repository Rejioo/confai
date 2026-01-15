from sqlalchemy.orm import Session
from models import Room

def resolve_room_id(db: Session, room_name: str):
    room = (
        db.query(Room)
        .filter(Room.name.ilike(f"%{room_name}%"))
        .first()
    )
    return room.id if room else None
