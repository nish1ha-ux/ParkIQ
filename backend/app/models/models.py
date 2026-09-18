import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
import enum
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class UserRole(str, enum.Enum):
    DRIVER = "DRIVER"
    STAFF = "STAFF"
    ADMIN = "ADMIN"

class SlotStatus(str, enum.Enum):
    VACANT = "VACANT"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"

class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    VIOLATION = "VIOLATION"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.DRIVER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    device_tokens = relationship("UserDeviceToken", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="user", cascade="all, delete-orphan")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    license_plate = Column(String(30), unique=True, index=True, nullable=False)
    vehicle_type = Column(String(30), default="SEDAN")  # SEDAN, SUV, EV, BIKE
    qr_token = Column(Text, nullable=True)  # AES-256 Encrypted Token String
    static_qr_token = Column(String(36), unique=True, nullable=True, index=True)  # Opaque static token for public QR
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="vehicles")
    sessions = relationship("ParkingSession", back_populates="vehicle")
    reservations = relationship("Reservation", back_populates="vehicle")

class ParkingLot(Base):
    __tablename__ = "parking_lots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(120), nullable=False)
    address = Column(String(255), nullable=False)
    total_slots = Column(Integer, default=50)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    base_hourly_rate = Column(Float, default=5.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    slots = relationship("ParkingSlot", back_populates="lot", cascade="all, delete-orphan")

class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lot_id = Column(String(36), ForeignKey("parking_lots.id"), nullable=False)
    slot_number = Column(String(20), nullable=False)
    floor_level = Column(Integer, default=1)
    slot_type = Column(String(20), default="STANDARD")  # STANDARD, EV, HANDICAP
    status = Column(SQLEnum(SlotStatus), default=SlotStatus.VACANT, nullable=False)

    lot = relationship("ParkingLot", back_populates="slots")
    sessions = relationship("ParkingSession", back_populates="slot")

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    slot_id = Column(String(36), ForeignKey("parking_slots.id"), nullable=False)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="ACTIVE")  # PENDING, ACTIVE, COMPLETED, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reservations")
    slot = relationship("ParkingSlot")
    vehicle = relationship("Vehicle", back_populates="reservations")

class ParkingSession(Base):
    __tablename__ = "parking_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False)
    slot_id = Column(String(36), ForeignKey("parking_slots.id"), nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow)
    predicted_departure = Column(DateTime, nullable=True)
    actual_exit_time = Column(DateTime, nullable=True)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False)
    qr_token_entry = Column(Text, nullable=True)

    vehicle = relationship("Vehicle", back_populates="sessions")
    slot = relationship("ParkingSlot", back_populates="sessions")
    payments = relationship("Payment", back_populates="session")
    fraud_alerts = relationship("FraudAlert", back_populates="session")
    notifications = relationship("NotificationLog", back_populates="session", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("parking_sessions.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    razorpay_order_id = Column(String(100), nullable=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ParkingSession", back_populates="payments")
    user = relationship("User", back_populates="payments")

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("parking_sessions.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # DUPLICATE_SCAN, EXPIRED_QR, UNMATCHED_ENTRY
    severity = Column(String(20), default="HIGH")
    details = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ParkingSession", back_populates="fraud_alerts")

class UserDeviceToken(Base):
    __tablename__ = "user_device_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="device_tokens")

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("parking_sessions.id"), nullable=True)
    event_type = Column(String(50), nullable=False)  # e.g., EXPIRES_IN_30, SECURITY_ALERT, etc.
    title = Column(String(100), nullable=False)
    body = Column(String(255), nullable=False)
    status = Column(String(20), default="SENT")  # SENT, FAILED
    sent_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
    session = relationship("ParkingSession", back_populates="notifications")
