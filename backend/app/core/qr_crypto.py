import json
import base64
import time
from typing import Dict, Any, Optional
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from app.config import settings

class QRCryptoEngine:
    """
    AES-256-GCM Encryption Engine for ParkIQ QR Digital Identities.
    Guarantees privacy-preserving QR tokens:
    - Encrypts payload with AES-256 authenticated encryption (GCM mode).
    - Exposes ZERO PII to public unauthenticated scanners.
    - Decryptable only by authorized ParkIQ staff/backend API keys.
    """
    def __init__(self, secret_key: Optional[str] = None):
        key_str = secret_key or settings.AES_QR_SECRET_KEY
        # Support hex-encoded 32-byte secret keys (64 characters)
        try:
            if len(key_str) == 64:
                self.key = bytes.fromhex(key_str)
            else:
                self.key = key_str.ljust(32, '0')[:32].encode('utf-8')
        except Exception:
            self.key = key_str.ljust(32, '0')[:32].encode('utf-8')

    def encrypt_vehicle_token(self, vehicle_id: str, owner_id: str, license_plate: str) -> str:
        """
        Encrypts vehicle identity into a secure Base64 QR payload token.
        Payload includes timestamp and nonce to prevent replay attacks.
        """
        payload = {
            "v_id": vehicle_id,
            "o_id": owner_id,
            "plate": license_plate,
            "ts": int(time.time()),
            "nonce": base64.b64encode(get_random_bytes(8)).decode('utf-8')
        }
        
        json_data = json.dumps(payload).encode('utf-8')
        nonce = get_random_bytes(12)  # GCM 96-bit nonce
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(json_data)
        
        # Combine nonce (12B) + tag (16B) + ciphertext
        raw_combined = nonce + tag + ciphertext
        return base64.urlsafe_b64encode(raw_combined).decode('utf-8')

    def decrypt_vehicle_token(self, token_b64: str) -> Dict[str, Any]:
        """Decrypts an AES-256 encrypted QR token payload.
        Raises ValueError if tampered or invalid.
        """
        try:
            raw_combined = base64.urlsafe_b64decode(token_b64.encode('utf-8'))
            if len(raw_combined) < 28:
                raise ValueError("QR Token payload too short")

            nonce = raw_combined[:12]
            tag = raw_combined[12:28]
            ciphertext = raw_combined[28:]

            cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
            decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)

            payload = json.loads(decrypted_data.decode('utf-8'))

            # Replay protection: verify timestamp is within validity window
            token_ts = payload.get("ts", 0)
            now = time.time()
            validity_window = getattr(settings, "QR_VALIDITY_WINDOW_SECONDS", 300)
            if now - token_ts > validity_window or token_ts - now > 60:
                raise ValueError("QR Token has expired (replay protection)")

            return payload
        except Exception as e:
            raise ValueError(f"Invalid or Tampered QR Token: {str(e)}")

    @staticmethod
    def mask_public_status(decrypted_payload: Dict[str, Any], session_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Filters decrypted payload into public non-sensitive status.
        Never exposes owner name, phone number, payment info, or exact user details.
        """
        masked_plate = decrypted_payload.get("plate", "")
        if len(masked_plate) > 4:
            masked_plate = masked_plate[:2] + "****" + masked_plate[-2:]
            
        status_data = {
            "status": "VALID_PARKIQ_VEHICLE",
            "masked_vehicle_id": decrypted_payload.get("v_id", "")[:8] + "...",
            "masked_license_plate": masked_plate,
            "session_active": False,
            "estimated_departure": None
        }
        
        if session_info:
            status_data.update({
                "session_active": session_info.get("is_active", False),
                "parking_slot": None,  # Hardening: Do not expose exact slot details publicly
                "estimated_departure": session_info.get("predicted_departure", "20 minutes"),
                "message": "Vehicle active in ParkIQ facility."
            })
        else:
            status_data["message"] = "Vehicle registered in ParkIQ system. No active parking session."
            
        return status_data

qr_crypto_engine = QRCryptoEngine()
