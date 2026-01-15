from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from time_utils import now_ist_naive
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from time_utils import now_ist_naive

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    bookings = relationship("Booking", back_populates="host")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)

    bookings = relationship("Booking", back_populates="room")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)  
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    meeting_type = Column(String, nullable=False)   # "online" | "offline"
    participants = Column(Text, nullable=True)      # "adam,julie"

    status = Column(String, default="booked")       # booked | in_use | cancelled
    created_at = Column(DateTime, default=now_ist_naive)

    room = relationship("Room", back_populates="bookings")
    host = relationship("User", back_populates="bookings")