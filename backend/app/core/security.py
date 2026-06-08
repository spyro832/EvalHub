import base64

from cryptography.fernet import Fernet

from app.core.config import settings


def _get_fernet() -> Fernet:
    # Pad/truncate secret key to exactly 32 bytes, then base64url-encode for Fernet
    key_bytes = settings.secret_key.encode()
    padded = key_bytes[:32].ljust(32, b"0")
    return Fernet(base64.urlsafe_b64encode(padded))


def encrypt_api_key(api_key: str) -> str:
    return _get_fernet().encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    return _get_fernet().decrypt(encrypted_key.encode()).decode()
