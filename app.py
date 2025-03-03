import os
import cv2
import numpy as np
import base64
import logging

from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import RequestEntityTooLarge

# ---------------------------
# Setup Flask & Security
# ---------------------------
app = Flask(__name__, template_folder='templates', static_folder='static')

# Use environment variable for the secret key (fallback provided for development)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_dev')
# Increased max file size to 10 MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """Check if file has a valid extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------
# Helper Functions
# ---------------------------
def image_to_base64(img, ext=".jpg"):
    success, buffer = cv2.imencode(ext, img)
    if not success:
        raise ValueError("Image encoding failed")
    img_as_text = base64.b64encode(buffer).decode('utf-8')
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime};base64,{img_as_text}"

def color_transfer(source, target):
    # Convert images to LAB color space for better color manipulation.
    source_lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype("float32")
    target_lab = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype("float32")
    
    (l_mean_src, a_mean_src, b_mean_src) = cv2.mean(source_lab)[:3]
    l_std_src = np.std(source_lab[:, :, 0])
    a_std_src = np.std(source_lab[:, :, 1])
    b_std_src = np.std(source_lab[:, :, 2])
    
    l_mean_tar = np.mean(target_lab[:, :, 0])
    a_mean_tar = np.mean(target_lab[:, :, 1])
    b_mean_tar = np.mean(target_lab[:, :, 2])
    
    l_std_tar = np.std(target_lab[:, :, 0])
    a_std_tar = np.std(target_lab[:, :, 1])
    b_std_tar = np.std(target_lab[:, :, 2])
    
    (l, a, b) = cv2.split(target_lab)
    l = ((l - l_mean_tar) * (l_std_src / (l_std_tar + 1e-8))) + l_mean_src
    a = ((a - a_mean_tar) * (a_std_src / (a_std_tar + 1e-8))) + a_mean_src
    b = ((b - b_mean_tar) * (b_std_src / (b_std_tar + 1e-8))) + b_mean_src
    
    transfer_lab = cv2.merge([l, a, b])
    transfer_lab = np.clip(transfer_lab, 0, 255).astype("uint8")
    transfer_bgr = cv2.cvtColor(transfer_lab, cv2.COLOR_LAB2BGR)
    return transfer_bgr

def simulate_color_blindness(image, deficiency):
    # Convert image to float [0,1] and then to RGB
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
    else:  # "normal" or unrecognized deficiency
        return image
    simulated = np.dot(image_rgb, M.T)
    simulated = np.clip(simulated, 0, 1)
    simulated_uint8 = (simulated * 255).astype(np.uint8)
    simulated_bgr = cv2.cvtColor(simulated_uint8, cv2.COLOR_RGB2BGR)
    return simulated_bgr

# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        sample_file = request.files.get('sample')
        user_file = request.files.get('user')
        if not sample_file or not user_file:
            return jsonify({'error': 'Missing file'}), 400
        
        # Validate file extensions
        if not (allowed_file(sample_file.filename) and allowed_file(user_file.filename)):
            return jsonify({'error': 'Unsupported file type'}), 400
        
        sample_bytes = np.frombuffer(sample_file.read(), np.uint8)
        user_bytes = np.frombuffer(user_file.read(), np.uint8)
        sample_img = cv2.imdecode(sample_bytes, cv2.IMREAD_COLOR)
        user_img = cv2.imdecode(user_bytes, cv2.IMREAD_COLOR)
        
        if sample_img is None or user_img is None:
            return jsonify({'error': 'Invalid image file'}), 400
        
        result_img = color_transfer(sample_img, user_img)
        encoded_img = image_to_base64(result_img, ".jpg")
        return jsonify({'result_img': encoded_img})
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
        
        # Validate file extension
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

# New contact submission route (replacing the PHP handler)
@app.route('/contact_submit', methods=['POST'])
def contact_submit():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        if not name or not email or not message:
            flash("All fields are required.", "error")
            return redirect(url_for('contact'))
        # Here you can add functionality to handle the contact submission
        logger.info("Contact submission from %s <%s>: %s", name, email, message)
        flash("Your message has been received. Thank you!", "success")
        return redirect(url_for('contact'))
    except Exception as e:
        logger.exception("Error in /contact_submit endpoint")
        flash("An error occurred. Please try again later.", "error")
        return redirect(url_for('contact'))

# Custom error handler for file size limit
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return jsonify({'error': 'File is too large. Maximum allowed size is 10 MB.'}), 413

# ---------------------------
# Run App
# ---------------------------
if __name__ == '__main__':
    # For local development. In production, use a WSGI server like Gunicorn.
    app.run(debug=False)