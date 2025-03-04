import json
import firebase_admin
from firebase_admin import credentials, storage
from config import Config

try:
    cred_input = Config.FIREBASE_CREDENTIALS
    # If cred_input starts with '{', assume it's a JSON string.
    if cred_input and cred_input.strip().startswith('{'):
        cred_dict = json.loads(cred_input)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate(cred_input)
    firebase_admin.initialize_app(cred, {
        'storageBucket': Config.FIREBASE_STORAGE_BUCKET
    })
    bucket = storage.bucket()
except Exception as e:
    print(f"Firebase initialization error: {e}")

def upload_file(file_stream, filename, content_type):
    try:
        blob = bucket.blob(filename)
        blob.upload_from_string(file_stream.read(), content_type=content_type)
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

def delete_file(filename):
    try:
        blob = bucket.blob(filename)
        blob.delete()
    except Exception as e:
        print(f"Error deleting file: {e}")

def list_files():
    return bucket.list_blobs()
