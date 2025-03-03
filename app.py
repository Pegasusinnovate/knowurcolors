import os
import json
import time
import cv2
import numpy as np
import base64
import logging
from threading import Timer

from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

# ---------------------------
# Firebase Setup for Python
# ---------------------------
import firebase_admin
from firebase_admin import credentials, storage

# Load Firebase credentials from environment variable (FIREBASE_CREDENTIALS contains the JSON string)
firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")
if firebase_creds_json:
    try:
        creds_dict = json.loads(firebase_creds_json)
        cred = credentials.Certificate(creds_dict)
    except Exception as e:
        raise Exception("Failed to load Firebase credentials from FIREBASE_CREDENTIALS") from e
else:
    # Alternatively, load from a file if available
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path:
        cred = credentials.Certificate(cred_path)
    else:
        raise Exception("No Firebase credentials provided. Set FIREBASE_CREDENTIALS or GOOGLE_APPLICATION_CREDENTIALS.")

firebase_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET")
if not firebase_bucket:
    raise Exception("FIREBASE_STORAGE_BUCKET environment variable not set.")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {'storageBucket': firebase_bucket})
bucket = storage.bucket()

# ---------------------------
# Setup Flask & Security
# ---------------------------
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_dev')
# Maximum allowed file size (10 MB by default)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  

csrf = CSRFProtect(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------
# Helper Functions for Firebase
# ---------------------------
def upload_to_firebase(file_obj, destination_path):
    blob = bucket.blob(destination_path)
    file_obj.seek(0)
    blob.upload_from_file(file_obj, content_type=file_obj.content_type)
    blob.make_public()
    return blob.public_url

def poll_for_processed_image(destination_path, timeout=30, interval=2):
    start_time = time.time()
    while time.time() - start_time < timeout:
        blob = bucket.blob(destination_path)
        if blob.exists():
            blob.make_public()
            return blob.public_url
        time.sleep(interval)
    return None

def delete_from_firebase(destination_path):
    blob = bucket.blob(destination_path)
    if blob.exists():
        blob.delete()
        logger.info("Deleted file from storage: %s", destination_path)

def schedule_delete(destination_path, delay=900):
    def delete_task():
        try:
            delete_from_firebase(destination_path)
            logger.info("Scheduled deletion completed for: %s", destination_path)
        except Exception as e:
            logger.exception("Error deleting file %s", destination_path)
    Timer(delay, delete_task).start()

def image_to_base64(img, ext=".jpg"):
    success, buffer = cv2.imencode(ext, img)
    if not success:
        raise ValueError("Image encoding failed")
    img_as_text = base64.b64encode(buffer).decode('utf-8')
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime};base64,{img_as_text}"

# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    """
    Uploads 'sample' and 'user' images to Firebase Storage.
    A Cloud Function (triggered by storage events) processes the 'user' image
    and writes the output to the 'processed/' folder. This endpoint polls for the
    processed file and returns its public URL.
    """
    try:
        sample_file = request.files.get('sample')
        user_file = request.files.get('user')
        if not sample_file or not user_file:
            return jsonify({'error': 'Missing file'}), 400

        if not (allowed_file(sample_file.filename) and allowed_file(user_file.filename)):
            return jsonify({'error': 'Unsupported file type'}), 400

        sample_filename = secure_filename(sample_file.filename)
        user_filename = secure_filename(user_file.filename)

        sample_path = f"uploads/sample_{sample_filename}"
        user_path = f"uploads/user_{user_filename}"

        sample_public_url = upload_to_firebase(sample_file, sample_path)
        user_public_url = upload_to_firebase(user_file, user_path)
        logger.info("Uploaded images: %s, %s", sample_public_url, user_public_url)

        # Cloud Function triggered by file uploads will process the 'user' file.
        # The processed file is expected at: processed/result_<user_filename>
        processed_path = f"processed/result_{user_filename}"
        logger.info("Waiting for processed image at: %s", processed_path)
        processed_public_url = poll_for_processed_image(processed_path)
        if not processed_public_url:
            return jsonify({'error': 'Processed image not found within timeout period.'}), 500

        # Remove original uploads immediately.
        delete_from_firebase(sample_path)
        delete_from_firebase(user_path)

        # Schedule deletion of the processed file after 15 minutes (900 seconds)
        schedule_delete(processed_path, delay=900)

        return jsonify({'result_img': processed_public_url})
    except Exception as e:
        logger.exception("Error in /process endpoint")
        return jsonify({'error': 'An error occurred during image processing.'}), 500

@app.route('/simulate_cb', methods=['POST'])
def simulate_cb():
    try:
        file = request.files.get('cbImage')
        deficiency = request.form.get('deficiency', 'normal')
        if not file:
            return jsonify({'error': 'Missing file'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file type'}), 400

        img_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({'error': 'Invalid image file'}), 400

        simulated_img = simulate_color_blindness(img, deficiency)
        encoded_img = image_to_base64(simulated_img, ".jpg")
        return jsonify({'simulated_img': encoded_img})
    except Exception as e:
        logger.exception("Error in /simulate_cb endpoint")
        return jsonify({'error': 'An error occurred during simulation.'}), 500

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/contact_submit', methods=['POST'])
def contact_submit():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        if not name or not email or not message:
            flash("All fields are required.", "error")
            return redirect(url_for('contact'))
        logger.info("Contact submission from %s <%s>: %s", name, email, message)
        flash("Your message has been received. Thank you!", "success")
        return redirect(url_for('contact'))
    except Exception as e:
        logger.exception("Error in /contact_submit endpoint")
        flash("An error occurred. Please try again later.", "error")
        return redirect(url_for('contact'))

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return jsonify({'error': 'File is too large. Maximum allowed size is 10 MB.'}), 413

# ---------------------------
# Utility: Color Blindness Simulation Function
# ---------------------------
def simulate_color_blindness(image, deficiency):
    image_float = image.astype(np.float32) / 255.0
    image_rgb = cv2.cvtColor(image_float, cv2.COLOR_BGR2RGB)
    if deficiency == "protanopia":
        M = np.array([[0.56667, 0.43333, 0],
                      [0.55833, 0.44167, 0],
                      [0,       0.24167, 0.75833]])
    elif deficiency == "deuteranopia":
        M = np.array([[0.625, 0.375, 0],
                      [0.70,  0.30,  0],
                      [0,     0.30,  0.70]])
    elif deficiency == "tritanopia":
        M = np.array([[0.95,    0.05,   0],
                      [0,       0.43333, 0.56667],
                      [0,       0.475,   0.525]])
    else:
        return image
    simulated = np.dot(image_rgb, M.T)
    simulated = np.clip(simulated, 0, 1)
    simulated_uint8 = (simulated * 255).astype(np.uint8)
    simulated_bgr = cv2.cvtColor(simulated_uint8, cv2.COLOR_RGB2BGR)
    return simulated_bgr

if __name__ == '__main__':
    # For local development; in production, use Gunicorn via the Procfile.
    app.run(debug=False)
