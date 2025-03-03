import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_dev')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    # Path to your Firebase service account key JSON file
    FIREBASE_CREDENTIALS = "C:\\Users\\mmdee\\Downloads\\urqrs-baf30-firebase-adminsdk-fbsvc-0544fffad7.json"
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'urqrs-baf30.firebasestorage.app')