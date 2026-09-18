from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.models import UserRole, SlotStatus, SessionStatus, PaymentStatus

# Auth Schemas
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role: Optional[UserRole] = UserRole.DRIVER

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Vehicle Schemas
class VehicleCreate(BaseModel):
    license_plate: str
    vehicle_type: Optional[str] = "SEDAN"

class VehicleResponse(BaseModel):
    id: str
    user_id: str
    license_plate: str
    vehicle_type: str
    qr_token: Optional[str] = None
    static_qr_token: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# QR Schemas
class QRVerifyRequest(BaseModel):
    qr_token: str

class PublicQRStatusResponse(BaseModel):
    status: str
    masked_vehicle_id: str
    masked_license_plate: str
    session_active: bool
    estimated_departure: Optional[str] = None
    parking_slot: Optional[str] = None
    message: Optional[str] = None

# Parking Lot & Slot Schemas
class SlotResponse(BaseModel):
    id: str
    lot_id: str
    slot_number: str
    floor_level: int
    slot_type: str
    status: SlotStatus

    class Config:
        from_attributes = True

class ParkingLotResponse(BaseModel):
    id: str
    name: str
    address: str
    total_slots: int
    base_hourly_rate: float
    slots: List[SlotResponse] = []

    class Config:
        from_attributes = True

# Parking Session Schemas
class StartSessionRequest(BaseModel):
    qr_token: str
    slot_id: str
    expected_duration_minutes: int = Field(default=60, ge=15, le=1440)

class EndSessionRequest(BaseModel):
    qr_token: str

class ExtendSessionRequest(BaseModel):
    additional_minutes: int = Field(default=30, ge=15, le=480)

class SessionResponse(BaseModel):
    id: str
    vehicle_id: str
    slot_id: str
    slot_number: Optional[str] = None
    entry_time: datetime
    expected_departure: datetime
    actual_exit_time: Optional[datetime] = None
    remaining_minutes: int
    is_expiring_soon: bool
    status: SessionStatus

    class Config:
        from_attributes = True

# AI & RAG Schemas
class AIPredictRequest(BaseModel):
    lot_id: str
    time_offset_hours: Optional[int] = 1

class AIPredictResponse(BaseModel):
    lot_id: str
    current_occupancy_pct: float
    predicted_occupancy_pct: float
    predicted_congestion_level: str
    recommended_slot_ids: List[str] = []
    average_predicted_duration_minutes: int

class RAGQueryRequest(BaseModel):
    question: str
    context_filter: Optional[str] = None

class RAGQueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[str] = []

# Payment Schemas
class PaymentCreateRequest(BaseModel):
    session_id: str

class PaymentVerifyRequest(BaseModel):
    payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

# Notification & Device Token Schemas
class DeviceTokenRegisterRequest(BaseModel):
    token: str

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str] = None
    event_type: str
    title: str
    body: str
    status: str
    sent_at: datetime

    class Config:
        from_attributes = True
