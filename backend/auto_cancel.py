from datetime import timedelta
from time_utils import now_ist_naive
from models import Booking

GRACE_MINUTES = 10

def auto_cancel_expired_bookings(db):
    now = now_ist_naive()
    deadline = now - timedelta(minutes=GRACE_MINUTES)

    expired = db.query(Booking).filter(
        Booking.status == "booked",
        Booking.start_time <= deadline
    ).all()

    for booking in expired:
        booking.status = "cancelled"

    if expired:
        db.commit()
