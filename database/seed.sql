-- =============================================================================
-- ParkIQ Smart Parking Intelligence Platform
-- PostgreSQL Seed Data SQL Script
-- =============================================================================

-- 1. Insert Initial Platform Users (Admin, Staff, Driver)
INSERT INTO users (id, full_name, email, phone, hashed_password, role) VALUES
('a0000000-0000-0000-0000-000000000001', 'Admin Manager', 'admin@parkiq.com', '+15550192834', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeg6Lruj3vjPGga31lW', 'ADMIN'),
('a0000000-0000-0000-0000-000000000002', 'John Staff', 'staff@parkiq.com', '+15550192835', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeg6Lruj3vjPGga31lW', 'STAFF'),
('a0000000-0000-0000-0000-000000000003', 'Alex Driver', 'driver@parkiq.com', '+15550192836', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeg6Lruj3vjPGga31lW', 'DRIVER');

-- 2. Insert Driver Vehicles with AES-256 Encrypted QR Tokens
INSERT INTO vehicles (id, user_id, license_plate, vehicle_type, aes_qr_token) VALUES
('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000003', 'KA-01-EQ-9988', 'SEDAN', 'ENC_AES256_PARKIQ_TOKEN_SAMPLE_9988'),
('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000003', 'MH-12-EV-4321', 'EV', 'ENC_AES256_PARKIQ_TOKEN_SAMPLE_4321');

-- 3. Insert Parking Facilities
INSERT INTO parking_lots (id, name, address, total_slots, latitude, longitude, base_hourly_rate) VALUES
('c0000000-0000-0000-0000-000000000001', 'Grand Central Multi-Level Garage', '100 Metro Boulevard, Tech District', 20, 37.7749, -122.4194, 6.50),
('c0000000-0000-0000-0000-000000000002', 'Apex Mall Plaza Lot', '45 Shopping Center Way', 15, 37.7833, -122.4167, 4.00);

-- 4. Insert Parking Slots for Grand Central Garage
INSERT INTO parking_slots (id, lot_id, slot_number, floor_level, slot_type, status) VALUES
('d0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'F1-A01', 1, 'EV', 'OCCUPIED'),
('d0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000002', 'F1-A02', 1, 'EV', 'RESERVED'),
('d0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000001', 'F1-A03', 1, 'HANDICAP', 'VACANT'),
('d0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000001', 'F1-A04', 1, 'STANDARD', 'OCCUPIED'),
('d0000000-0000-0000-0000-000000000005', 'c0000000-0000-0000-0000-000000000001', 'F1-A05', 1, 'STANDARD', 'VACANT');

-- 5. Insert Active Parking Session
INSERT INTO parking_sessions (id, vehicle_id, slot_id, entry_time, predicted_departure, status, qr_token_entry) VALUES
('e0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 'd0000000-0000-0000-0000-000000000001', CURRENT_TIMESTAMP - INTERVAL '45 minutes', CURRENT_TIMESTAMP + INTERVAL '75 minutes', 'ACTIVE', 'ENC_AES256_PARKIQ_TOKEN_SAMPLE_9988');

-- 6. Insert Financial Payment Record
INSERT INTO payments (id, session_id, user_id, amount, payment_status, razorpay_order_id, razorpay_payment_id) VALUES
('f0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000003', 6.50, 'PAID', 'order_parkiq_demo_1001', 'pay_parkiq_demo_9001');
