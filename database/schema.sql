-- =============================================================================
-- ParkIQ Smart Parking Intelligence Platform
-- Enterprise PostgreSQL Database Schema DDL
-- =============================================================================

-- Enable UUID extension for cryptographic primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- CUSTOM ENUM TYPES
-- -----------------------------------------------------------------------------

CREATE TYPE user_role_enum AS ENUM ('DRIVER', 'STAFF', 'ADMIN');
CREATE TYPE slot_type_enum AS ENUM ('STANDARD', 'EV', 'HANDICAP', 'VIP');
CREATE TYPE slot_status_enum AS ENUM ('VACANT', 'OCCUPIED', 'RESERVED', 'OUT_OF_SERVICE');
CREATE TYPE session_status_enum AS ENUM ('ACTIVE', 'CLOSED', 'VIOLATION');
CREATE TYPE payment_status_enum AS ENUM ('PENDING', 'PAID', 'FAILED', 'REFUNDED');
CREATE TYPE alert_severity_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

-- -----------------------------------------------------------------------------
-- TABLE: users
-- Stores registered platform users (Drivers, Parking Staff, Facility Admins)
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20),
    hashed_password VARCHAR(255) NOT NULL,
    role user_role_enum NOT NULL DEFAULT 'DRIVER',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- -----------------------------------------------------------------------------
-- TABLE: vehicles
-- Stores registered driver vehicles linked to AES-256 encrypted QR tokens
-- -----------------------------------------------------------------------------
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    license_plate VARCHAR(30) UNIQUE NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL DEFAULT 'SEDAN',
    aes_qr_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vehicles_user_id ON vehicles(user_id);
CREATE INDEX idx_vehicles_license_plate ON vehicles(license_plate);

-- -----------------------------------------------------------------------------
-- TABLE: parking_lots
-- Stores parking facilities (garages, plazas, airports, campus lots)
-- -----------------------------------------------------------------------------
CREATE TABLE parking_lots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(120) NOT NULL,
    address VARCHAR(255) NOT NULL,
    total_slots INT NOT NULL DEFAULT 50 CHECK (total_slots > 0),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    base_hourly_rate DECIMAL(10, 2) NOT NULL DEFAULT 5.00 CHECK (base_hourly_rate >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_parking_lots_coords ON parking_lots(latitude, longitude);

-- -----------------------------------------------------------------------------
-- TABLE: parking_slots
-- Individual physical parking bays/slots within a facility
-- -----------------------------------------------------------------------------
CREATE TABLE parking_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lot_id UUID NOT NULL REFERENCES parking_lots(id) ON DELETE CASCADE,
    slot_number VARCHAR(20) NOT NULL,
    floor_level INT NOT NULL DEFAULT 1,
    slot_type slot_type_enum NOT NULL DEFAULT 'STANDARD',
    status slot_status_enum NOT NULL DEFAULT 'VACANT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_lot_slot_number UNIQUE (lot_id, slot_number)
);

CREATE INDEX idx_parking_slots_lot_id ON parking_slots(lot_id);
CREATE INDEX idx_parking_slots_status ON parking_slots(status);

-- -----------------------------------------------------------------------------
-- TABLE: reservations
-- Advance parking spot bookings by drivers
-- -----------------------------------------------------------------------------
CREATE TABLE reservations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slot_id UUID NOT NULL REFERENCES parking_slots(id) ON DELETE CASCADE,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CHECK (end_time > start_time)
);

CREATE INDEX idx_reservations_user_id ON reservations(user_id);
CREATE INDEX idx_reservations_times ON reservations(start_time, end_time);

-- -----------------------------------------------------------------------------
-- TABLE: parking_sessions
-- Real-time active and historical parking check-in/check-out sessions
-- -----------------------------------------------------------------------------
CREATE TABLE parking_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    slot_id UUID NOT NULL REFERENCES parking_slots(id) ON DELETE CASCADE,
    entry_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    predicted_departure TIMESTAMP WITH TIME ZONE,
    actual_exit_time TIMESTAMP WITH TIME ZONE,
    status session_status_enum NOT NULL DEFAULT 'ACTIVE',
    qr_token_entry TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_vehicle_id ON parking_sessions(vehicle_id);
CREATE INDEX idx_sessions_slot_id ON parking_sessions(slot_id);
CREATE INDEX idx_sessions_status ON parking_sessions(status);

-- -----------------------------------------------------------------------------
-- TABLE: payments
-- Financial transaction records linked to parking sessions and Razorpay
-- -----------------------------------------------------------------------------
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES parking_sessions(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),
    payment_status payment_status_enum NOT NULL DEFAULT 'PENDING',
    razorpay_order_id VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_session_id ON payments(session_id);

-- -----------------------------------------------------------------------------
-- TABLE: fraud_alerts
-- Log of AI-detected security anomalies, duplicate QR scans, and violations
-- -----------------------------------------------------------------------------
CREATE TABLE fraud_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES parking_sessions(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity alert_severity_enum NOT NULL DEFAULT 'HIGH',
    details TEXT,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fraud_alerts_resolved ON fraud_alerts(resolved);
CREATE INDEX idx_fraud_alerts_severity ON fraud_alerts(severity);

-- -----------------------------------------------------------------------------
-- TRIGGER FUNCTION: Automatic updated_at timestamp refresher
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_timestamp_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE update_timestamp_column();
CREATE TRIGGER trg_vehicles_updated_at BEFORE UPDATE ON vehicles FOR EACH ROW EXECUTE PROCEDURE update_timestamp_column();
