import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///../database/faults.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
