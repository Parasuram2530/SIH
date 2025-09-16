import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/civic_reporter")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
    UPLOAD_FOLDER = os.getenv("UPLOAD_DIR", "./uploads")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
    PORT = int(os.getenv("PORT", 5000))