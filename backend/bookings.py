from sqlalchemy.orm import Session
from models import Booking
from datetime import datetime

def is_room_available(db: Session, room_id: int, start: datetime, end: datetime):
    conflict = db.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.status != "cancelled",
        Booking.start_time < end,
        Booking.end_time > start
    ).first()

    return conflict is None
