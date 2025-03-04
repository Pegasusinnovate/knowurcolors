import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_dev')
    MAX_CONTENT_LENGTH = 50 * 1920 * 1080  # 50 MB
    # Path to your Firebase service account key JSON file
    FIREBASE_CREDENTIALS = os.environ.get('FIREBASE_CREDENTIALS')
    FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET')
