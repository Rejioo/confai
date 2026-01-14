from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
Base.metadata.create_all(bind=engine)
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import hash_password, verify_password, create_access_token
from rooms import seed_rooms
from database import SessionLocal
from models import Room
from bookings import is_room_available
from datetime import datetime
from auth import decode_token
# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import Booking
from auto_cancel import auto_cancel_expired_bookings
from time_utils import now_ist_naive
from sqlalchemy import distinct

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     payload = decode_token(token)
#     if not payload:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     user = db.query(User).filter(User.id == payload["user_id"]).first()
#     if not user:
#         raise HTTPException(status_code=401, detail="User not found")

#     return user
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

db = SessionLocal()
seed_rooms(db)
db.close()

app = FastAPI(title="ConfAI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo mode, calm down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/register")
def register(name: str, email: str, password: str, db: Session = Depends(get_db)):
    if not email.endswith("@company.com"):
        raise HTTPException(status_code=403, detail="Only company employees allowed")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        name=name,
        email=email,
        password=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully"}

@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id, "email": user.email})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.get("/rooms")
def list_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).all()
    return rooms



@app.post("/book-room")
def book_room(
    room_id: int,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Normalize to IST-naive (ASSUME input is IST)
    start_time = start_time.replace(tzinfo=None)
    end_time = end_time.replace(tzinfo=None)
    
    if not is_room_available(db, room_id, start_time, end_time):
        raise HTTPException(status_code=400, detail="Room not available")

    booking = Booking(
        room_id=room_id,
        host_id=user.id,
        start_time=start_time,
        end_time=end_time
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return {"message": "Room booked successfully", "booking_id": booking.id}

@app.get("/dashboard/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    now = now_ist_naive()

    total_rooms = db.query(Room).count()

    rooms_in_use = db.query(distinct(Booking.room_id)).filter(
        Booking.status == "in_use",
        Booking.start_time <= now,
        Booking.end_time >= now
    ).count()

    rooms_booked_now = db.query(distinct(Booking.room_id)).filter(
        Booking.status == "booked",
        Booking.start_time <= now,
        Booking.end_time >= now
    ).count()

    available_rooms = total_rooms - rooms_in_use - rooms_booked_now
    upcoming_bookings = db.query(Booking).filter(
    Booking.status == "booked",
    Booking.start_time > now
    ).count()

    return {
        "total_rooms": total_rooms,
        "available_rooms": max(available_rooms, 0),
        "rooms_in_use": rooms_in_use,
        "rooms_booked": rooms_booked_now,
        "upcoming bookings":upcoming_bookings
    }
    
@app.get("/my-schedules")
def my_schedules(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    auto_cancel_expired_bookings(db)

    bookings = db.query(Booking).filter(
        Booking.host_id == user.id
    ).order_by(Booking.start_time).all()

    return bookings
