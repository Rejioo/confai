from sqlalchemy.orm import Session
from models import Room

def seed_rooms(db: Session):
    if db.query(Room).count() > 0:
        return

    rooms = [
        Room(name="Conference Room A", capacity=10),
        Room(name="Conference Room B", capacity=8),
        Room(name="Huddle Room 1", capacity=4),
        Room(name="Huddle Room 2", capacity=4),
    ]

    db.add_all(rooms)
    db.commit()
