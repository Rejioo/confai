from datetime import datetime
from sqlalchemy.orm import Session
from models import Booking

def create_booking(
    db: Session,
    host_id: int,
    room_id: int | None,
    date: str,
    start_time: str,
    end_time: str,
    meeting_type: str,          # "online" | "offline"
    participants: list[str]
):
    start_dt = datetime.fromisoformat(f"{date}T{start_time}")
    end_dt   = datetime.fromisoformat(f"{date}T{end_time}")

    booking = Booking(
        room_id=room_id,
        host_id=host_id,
        start_time=start_dt,
        end_time=end_dt,
        meeting_type=meeting_type,
        participants=",".join(participants),
        status="booked",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
