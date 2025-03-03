import cv2
import numpy as np
from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash, current_app
from werkzeug.exceptions import RequestEntityTooLarge
from .image_processing import color_transfer, simulate_color_blindness, image_to_base64
from .firebase_utils import upload_file

main_blueprint = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_blueprint.route('/')
def index():
    return render_template('index.html')

@main_blueprint.route('/process', methods=['POST'])
def process():
    try:
        sample_file = request.files.get('sample')
        user_file = request.files.get('user')
        
        if not sample_file or not user_file:
            return jsonify({'error': 'Missing file'}), 400
        
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
        current_app.logger.exception("Error in /process endpoint")
        return jsonify({'error': 'An error occurred during image processing.'}), 500

@main_blueprint.route('/simulate_cb', methods=['POST'])
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
        current_app.logger.exception("Error in /simulate_cb endpoint")
        return jsonify({'error': 'An error occurred during simulation.'}), 500

@main_blueprint.route('/upload_firebase', methods=['POST'])
def upload_firebase():
    try:
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported or missing file'}), 400
        filename = f"{int(time.time())}_{file.filename}"
        public_url = upload_file(file, filename, file.content_type)
        return jsonify({'file_url': public_url})
    except Exception as e:
        current_app.logger.exception("Error in /upload_firebase endpoint")
        return jsonify({'error': 'An error occurred during file upload.'}), 500

@main_blueprint.route('/contact_submit', methods=['POST'])
def contact_submit():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        if not name or not email or not message:
            flash("All fields are required.", "error")
            return redirect(url_for('main.contact'))
        current_app.logger.info("Contact submission from %s <%s>: %s", name, email, message)
        flash("Your message has been received. Thank you!", "success")
        return redirect(url_for('main.contact'))
    except Exception as e:
        current_app.logger.exception("Error in /contact_submit endpoint")
        flash("An error occurred. Please try again later.", "error")
        return redirect(url_for('main.contact'))

@main_blueprint.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main_blueprint.route('/terms')
def terms():
    return render_template('terms.html')

@main_blueprint.route('/about')
def about():
    return render_template('about.html')

@main_blueprint.route('/contact')
def contact():
    return render_template('contact.html')

@main_blueprint.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return jsonify({'error': 'File is too large. Maximum allowed size is 10 MB.'}), 413