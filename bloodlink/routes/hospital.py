from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from firebase.firestore_service import create_hospital_request
from ml.forecast import predict_blood_demand
from werkzeug.utils import secure_filename
import os

hospital_bp = Blueprint('hospital', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@hospital_bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        hospital_name = request.form.get('hospital_name')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        address = request.form.get('address')
        
        # Store hospital info in session
        session['hospital_name'] = hospital_name
        session['hospital_location'] = {
            'latitude': float(latitude),
            'longitude': float(longitude),
            'address': address
        }
        
        flash('Hospital information saved!', 'success')
        return redirect(url_for('hospital.dashboard'))
    
    hospital_name = session.get('hospital_name', '')
    return render_template('hospital_dashboard.html', hospital_name=hospital_name)

@hospital_bp.route('/predict-demand', methods=['POST'])
def predict_demand():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Run prediction
        result = predict_blood_demand(filepath)
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify(result)
    
    return jsonify({'success': False, 'error': 'Invalid file format'})

@hospital_bp.route('/emergency-request', methods=['POST'])
def emergency_request():
    hospital_name = session.get('hospital_name')
    hospital_location = session.get('hospital_location')
    
    if not hospital_name or not hospital_location:
        return jsonify({'success': False, 'error': 'Hospital information not set'})
    
    blood_type = request.form.get('blood_type')
    units = request.form.get('units')
    urgency = request.form.get('urgency', 'high')
    
    result = create_hospital_request(hospital_name, hospital_location, blood_type, units, urgency)
    
    if result['success']:
        flash('Emergency blood request sent!', 'success')
    else:
        flash(f'Error: {result["error"]}', 'error')
    
    return redirect(url_for('hospital.dashboard'))