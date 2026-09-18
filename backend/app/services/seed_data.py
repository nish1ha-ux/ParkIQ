from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models.models import User, Vehicle, ParkingLot, ParkingSlot, ParkingSession, UserRole, SlotStatus, SessionStatus
from app.core.security import get_password_hash
from app.core.qr_crypto import qr_crypto_engine

def seed_database():
    """
    Initializes database schema and populates initial demonstration data.
    """
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if users already exist
        if db.query(User).first():
            print("[Seed Data] Database already seeded.")
            return

        print("[Seed Data] Seeding ParkIQ database with initial entities...")

        # 1. Create Users
        admin_user = User(
            full_name="Admin Manager",
            email="admin@parkiq.com",
            phone="+15550192834",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        staff_user = User(
            full_name="John Staff",
            email="staff@parkiq.com",
            phone="+15550192835",
            hashed_password=get_password_hash("staff123"),
            role=UserRole.STAFF
        )
        driver_user = User(
            full_name="Alex Driver",
            email="driver@parkiq.com",
            phone="+15550192836",
            hashed_password=get_password_hash("driver123"),
            role=UserRole.DRIVER
        )

        db.add_all([admin_user, staff_user, driver_user])
        db.flush()

        # 2. Create Vehicles for Driver
        v1 = Vehicle(
            user_id=driver_user.id,
            license_plate="KA-01-EQ-9988",
            vehicle_type="SEDAN"
        )
        v2 = Vehicle(
            user_id=driver_user.id,
            license_plate="MH-12-EV-4321",
            vehicle_type="EV"
        )
        db.add_all([v1, v2])
        db.flush()

        # Generate AES-256 Encrypted QR Tokens
        v1.qr_token = qr_crypto_engine.encrypt_vehicle_token(v1.id, driver_user.id, v1.license_plate)
        v2.qr_token = qr_crypto_engine.encrypt_vehicle_token(v2.id, driver_user.id, v2.license_plate)

        # 3. Create Parking Lots
        lot1 = ParkingLot(
            name="Grand Central Multi-Level Garage",
            address="100 Metro Boulevard, Tech District",
            total_slots=20,
            latitude=37.7749,
            longitude=-122.4194,
            base_hourly_rate=6.50
        )
        lot2 = ParkingLot(
            name="Apex Mall Plaza Lot",
            address="45 Shopping Center Way",
            total_slots=15,
            latitude=37.7833,
            longitude=-122.4167,
            base_hourly_rate=4.00
        )
        db.add_all([lot1, lot2])
        db.flush()

        # 4. Create Slots for Lot 1
        created_slots = []
        for floor in [1, 2]:
            for num in range(1, 11):
                slot_code = f"F{floor}-A{num:02d}"
                stype = "EV" if num <= 2 else ("HANDICAP" if num == 3 else "STANDARD")
                status = SlotStatus.VACANT
                if floor == 1 and num in [1, 4, 5, 7]:
                    status = SlotStatus.OCCUPIED
                elif floor == 1 and num == 2:
                    status = SlotStatus.RESERVED

                slot = ParkingSlot(
                    lot_id=lot1.id,
                    slot_number=slot_code,
                    floor_level=floor,
                    slot_type=stype,
                    status=status
                )
                db.add(slot)
                created_slots.append(slot)

        db.flush()

        # 5. Create Active Parking Session
        occupied_slot = [s for s in created_slots if s.status == SlotStatus.OCCUPIED][0]
        session1 = ParkingSession(
            vehicle_id=v1.id,
            slot_id=occupied_slot.id,
            entry_time=datetime.utcnow() - timedelta(minutes=45),
            predicted_departure=datetime.utcnow() + timedelta(minutes=75),
            status=SessionStatus.ACTIVE,
            qr_token_entry=v1.qr_token
        )
        db.add(session1)

        db.commit()
        print("[Seed Data] ParkIQ database successfully seeded!")
    except Exception as e:
        db.rollback()
        print(f"[Seed Data] Seeding error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
