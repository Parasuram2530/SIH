# auth.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, decode_token
from datetime import timedelta

def hash_password(password):
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(password, hashed):
    return check_password_hash(hashed, password)

def create_token(identity: dict):
    access_token = create_access_token(identity=identity, expires_delta=timedelta(days=7))
    return access_token

def get_identity_from_token(raw_token: str):
    try:
        data = decode_token(raw_token)
        return data.get("identity")
    except Exception:
        return None