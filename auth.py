from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, decode_token
from datetime import timedelta

def hash_password(plain: str) -> str:
    return generate_password_hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return check_password_hash(hashed, plain)

def create_token(identity: dict):
    access_token = create_access_token(identity=identity, expires_delta=timedelta(days=7))
    return access_token

def get_identity_from_token(raw_token: str):
    try:
        data = decode_token(raw_token)
        return data.get("identity")
    except Exception:
        return None