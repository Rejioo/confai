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
from fastapi import HTTPException
from schemas.chat_intent import ChatIntent
from chat_llm import call_llm
from participant_utils import extract_participants_from_text
from room_utils import extract_room_name
from time_parser import extract_date_time
from typing import Dict
from datetime import datetime
import re
from intent_utils import infer_intent_from_text
from booking_service import create_booking
from room_resolver import resolve_room_id
from bookings import is_room_available
from datetime import datetime
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     payload = decode_token(token)
#     if not payload:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     user = db.query(User).filter(User.id == payload["user_id"]).first()
#     if not user:
#         raise HTTPException(status_code=401, detail="User not found")

#     return user
pending_bookings: Dict[int, dict] = {}

def empty_booking(intent: str):
    return {
        "intent": intent,               # online / offline / unknown
        "room_name": None,
        "date": None,
        "start_time": None,
        "end_time": None,
        "participants": []
    }
pending_bookings = {}
def empty_booking(intent: str):
    return {
        "intent": intent,
        "room_name": None,
        "date": None,
        "start_time": None,
        "end_time": None,
        "participants": []
    }
def merge_booking(existing: dict, new: dict):
    for key, value in new.items():
        if value is None:
            continue
        if key == "participants":
            if value:
                existing["participants"] = list(set(existing["participants"] + value))
        else:
            existing[key] = value


















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
    # if not email.endswith("@company.com"):
    #     raise HTTPException(status_code=403, detail="Only company employees allowed")
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

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

    upcoming_bookings = db.query(Booking).filter(
        Booking.status == "booked",
        Booking.start_time > now
    ).count()

    available_rooms = total_rooms - rooms_in_use - rooms_booked_now

    return {
        "total_rooms": total_rooms,
        "available_rooms": max(available_rooms, 0),
        "rooms_in_use": rooms_in_use,
        "rooms_booked": rooms_booked_now,
        "upcoming_bookings": upcoming_bookings
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


@app.post("/check-in")
def check_in(
    booking_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    now = now_ist_naive()

    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status != "booked":
        raise HTTPException(status_code=400, detail="Booking not eligible for check-in")

    if not (booking.start_time <= now <= booking.end_time):
        raise HTTPException(
            status_code=400,
            detail="Check-in allowed only during meeting time"
        )

    booking.status = "in_use"
    db.commit()

    return {
        "message": "Checked in successfully",
        "room_id": booking.room_id
    }
    


@app.post("/chat")
def chat(
    message: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    user_id = user.id
    msg = message.lower()
    
    # -------------------------------
    # 1. INTENT RESOLUTION
    # -------------------------------

    # rule-based intent (strong signals)
    rule_intent = infer_intent_from_text(msg)

    # llm intent (weak / fallback)
    llm_intent = call_llm(message).get("intent", "unknown")

    if rule_intent != "unknown":
        intent_type = rule_intent
    else:
        intent_type = llm_intent

    # -------------------------------
    # 2. CREATE / FETCH BOOKING STATE
    # -------------------------------

    if user_id not in pending_bookings:
        pending_bookings[user_id] = empty_booking(intent_type)

    booking = pending_bookings[user_id]

    # upgrade intent if previously unknown
    if booking["intent"] == "unknown" and intent_type != "unknown":
        booking["intent"] = intent_type

    # fallback: room implies offline
    if booking["intent"] == "unknown" and extract_room_name(msg):
        booking["intent"] = "book_offline_meeting"

    # still unknown → ASK
    if booking["intent"] == "unknown":
        return {
            "type": "ask",
            "message": "Is this an online or offline meeting?"
        }

    # -------------------------------
    # 3. SLOT EXTRACTION
    # -------------------------------
    from participant_llm import extract_participants_llm

    extracted = {
        "room_name": extract_room_name(msg),
        # "participants": extract_participants_from_text(msg)
        "participants": extract_participants_from_text(msg)

    }

    date, parsed_start, parsed_end = extract_date_time(msg)
    extracted["date"] = date
    
    # time handling (context-aware)
    if parsed_start and not booking["start_time"]:
        extracted["start_time"] = parsed_start
    elif parsed_start and booking["start_time"] and not booking["end_time"]:
        extracted["end_time"] = parsed_start

    if parsed_end:
        extracted["end_time"] = parsed_end

    # merge into booking
    merge_booking(booking, extracted)

    # -------------------------------
    # 4. SLOT VALIDATION
    # -------------------------------

    missing = []

    if booking["intent"] == "book_offline_meeting":
        if not booking["room_name"]:
            missing.append("room name")

    if not booking["date"]:
        missing.append("date")
    if not booking["start_time"]:
        missing.append("start time")
    if not booking["end_time"]:
        missing.append("end time")
    if not booking["participants"]:
        missing.append("participants")

    # -------------------------------
    # 5. ASK OR CONFIRM
    # -------------------------------

    if missing:
        return {
            "type": "ask",
            "message": f"I need the following details: {', '.join(missing)}"
        }

    # confirmed → cleanup state
    confirmed_booking = booking.copy()
    del pending_bookings[user_id]

    # -------------------------------
    # CREATE BOOKING AFTER CONFIRM
    # -------------------------------

    booking_data = confirmed_booking

    # map intent -> meeting_type
    meeting_type = (
        "offline"
        if booking_data["intent"] == "book_offline_meeting"
        else "online"
    )
    
    room_id=None
    # -------------------------------
    # FINAL VALIDATION BEFORE BOOKING
    # -------------------------------

    required = ["date", "start_time", "end_time"]
    missing = [k for k in required if not booking_data.get(k)]

    if missing:
        return {
            "type": "ask",
            "message": f"I need the following details: {', '.join(missing)}"
        }

    if meeting_type == "offline" and not booking_data.get("room_name"):
        return {
            "type": "ask",
            "message": "Which room should I book?"
        }

    if not booking_data.get("participants"):
        return {
            "type": "ask",
            "message": "Who are the participants?"
        }
    
    # start_dt = datetime.fromisoformat(
    #     f"{booking_data['date']}T{booking_data['start_time']}"
    # )
    # end_dt = datetime.fromisoformat(
    #     f"{booking_data['date']}T{booking_data['end_time']}"
    # )

    # # check overlap only for offline meetings
    # if meeting_type == "offline":
    #     if not is_room_available(db, room_id, start_dt, end_dt):
    #         return {
    #             "type": "error",
    #             "message": "Room is already booked for this time slot."
    #         }
    
  
    # # resolve room for offline
    # 
    # if meeting_type == "offline":
    #     room_id = resolve_room_id(db, booking_data["room_name"])
    #     if not room_id:
    #         return {
    #             "type": "error",
    #             "message": f"Room '{booking_data['room_name']}' not found."
    #         }
    room_id = None
    
    
    # resolve room_id + overlap check ONLY for offline meetings
    if meeting_type == "offline":
        room_id = resolve_room_id(db, booking_data["room_name"])
        if not room_id:
            return {
                "type": "error",
                "message": f"Room '{booking_data['room_name']}' not found."
            }

        start_dt = datetime.fromisoformat(
            f"{booking_data['date']}T{booking_data['start_time']}"
        )
        end_dt = datetime.fromisoformat(
            f"{booking_data['date']}T{booking_data['end_time']}"
        )

        if not is_room_available(db, room_id, start_dt, end_dt):
            return {
                "type": "error",
                "message": "Room is already booked for this time slot."
            }

    
    
    
    
    # create booking
    try:
        new_booking = create_booking(
            db=db,
            host_id=user.id,
            room_id=room_id,
            date=booking_data["date"],
            start_time=booking_data["start_time"],
            end_time=booking_data["end_time"],
            meeting_type=meeting_type,
            participants=booking_data["participants"],
        )
    except Exception as e:
        db.rollback()
        return {
            "type": "error",
            "message": f"Booking failed: {str(e)}"
        }
    
        # -------- EMAIL NOTIFICATION --------
    from email_service import send_email

    participant_names = booking_data["participants"]

    users = (
        db.query(User)
        .filter(User.name.in_(participant_names))
        .all()
    )

    emails = [u.email for u in users]

    if emails:
        subject = "Meeting Scheduled"

        body = f"""
    Meeting Details:

    Type: {meeting_type}
    Room: {booking_data.get("room_name", "Online")}
    Date: {booking_data['date']}
    Time: {booking_data['start_time']} to {booking_data['end_time']}
    Host: {user.name}
    """

        try:
            send_email(
                to_emails=emails,
                subject=subject,
                body=body
            )
        except Exception as e:
            print("EMAIL FAILED:", e)
    # -------- END EMAIL --------

    # IMPORTANT: clear state
    pending_bookings.pop(user.id, None)

    return {
        "type": "success",
        "message": "Meeting booked successfully.",
        "booking_id": new_booking.id
    }
        
    
    
    
