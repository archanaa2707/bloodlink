from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from firebase.firestore_service import (
    create_blood_request, get_pending_requests, accept_donation_slot,
    get_user_requests, get_user_donations, update_user_location,
    verify_donation, get_request_donations, delete_user_donation
)
from firebase.auth_service import get_user_data
from functools import wraps

people_bp = Blueprint('people', __name__)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'uid' not in session:
            # For API endpoints, return JSON error
            if request.path.startswith('/people/accept-') or request.path.startswith('/people/verify-'):
                return jsonify({'success': False, 'error': 'Not logged in. Please refresh and login again.'}), 401
            flash('Please login first', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@people_bp.route('/check-login')
def check_login():
    """Check if user is logged in"""
    if 'uid' in session:
        return jsonify({'success': True, 'logged_in': True, 'uid': session.get('uid')})
    else:
        return jsonify({'success': False, 'logged_in': False})

@people_bp.route('/dashboard')
@login_required
def dashboard():
    uid = session.get('uid')
    user_result = get_user_data(uid)
    
    if user_result['success']:
        user_data = user_result['data']
        return render_template('people_dashboard.html', user=user_data)
    else:
        flash('Error loading dashboard', 'error')
        return redirect(url_for('auth.login'))

@people_bp.route('/request-blood', methods=['GET', 'POST'])
@login_required
def request_blood():
    if request.method == 'POST':
        uid = session.get('uid')
        blood_type = request.form.get('blood_type')
        units = request.form.get('units')
        special_requirements = request.form.get('special_requirements', '')
        
        # Location data from form
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        address = request.form.get('address')
        
        location = {
            'latitude': float(latitude),
            'longitude': float(longitude),
            'address': address
        }
        
        result = create_blood_request(uid, blood_type, units, location, special_requirements)
        
        if result['success']:
            flash('Blood request created successfully!', 'success')
            return redirect(url_for('people.orders'))
        else:
            flash(f'Error: {result["error"]}', 'error')
    
    return render_template('request_blood.html')

@people_bp.route('/donate-blood')
@login_required
def donate_blood():
    # Get all pending requests
    result = get_pending_requests()
    
    if result['success']:
        requests = result['requests']
        return render_template('donate_blood.html', requests=requests)
    else:
        flash(f'Error: {result["error"]}', 'error')
        return render_template('donate_blood.html', requests=[])

@people_bp.route('/accept-donation/<request_id>', methods=['POST'])
@login_required
def accept_donation(request_id):
    try:
        uid = session.get('uid')
        print(f"Accept donation called: request_id={request_id}, uid={uid}")
        
        # Get JSON data
        data = request.get_json()
        print(f"Received data: {data}")
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        donation_date = data.get('donation_date')
        donation_time = data.get('donation_time')
        
        if not donation_date or not donation_time:
            return jsonify({'success': False, 'error': 'Date and time required'}), 400
        
        print(f"Calling accept_donation_slot with date={donation_date}, time={donation_time}")
        result = accept_donation_slot(request_id, uid, donation_date, donation_time)
        print(f"Result: {result}")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"ERROR in accept_donation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@people_bp.route('/verify-donation/<request_id>', methods=['POST'])
@login_required
def verify_donation_route(request_id):
    try:
        data = request.get_json()
        verification_code = data.get('code')
        
        if not verification_code:
            return jsonify({'success': False, 'error': 'Verification code required'}), 400
        
        result = verify_donation(request_id, verification_code)
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in verify_donation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@people_bp.route('/delete-donation/<donation_id>', methods=['POST'])
@login_required
def delete_donation(donation_id):
    try:
        uid = session.get('uid')
        
        result = delete_user_donation(donation_id, uid)
        
        if result['success']:
            flash('Donation cancelled successfully', 'success')
        else:
            flash(f'Error: {result["error"]}', 'error')
        
        return redirect(url_for('people.orders'))
        
    except Exception as e:
        print(f"Error in delete_donation: {str(e)}")
        flash('Error deleting donation', 'error')
        return redirect(url_for('people.orders'))

@people_bp.route('/orders')
@login_required
def orders():
    uid = session.get('uid')
    
    # Get user's requests
    requests_result = get_user_requests(uid)
    donations_result = get_user_donations(uid)
    
    user_requests = requests_result['requests'] if requests_result['success'] else []
    user_donations = donations_result['donations'] if donations_result['success'] else []
    
    return render_template('orders.html', requests=user_requests, donations=user_donations)

@people_bp.route('/credits')
@login_required
def credits():
    uid = session.get('uid')
    user_result = get_user_data(uid)
    
    if user_result['success']:
        user_data = user_result['data']
        blood_credits = user_data.get('blood_credits', 0)
        return render_template('credits.html', credits=blood_credits)
    else:
        flash('Error loading credits', 'error')
        return redirect(url_for('people.dashboard'))

@people_bp.route('/request-details/<request_id>')
@login_required
def request_details(request_id):
    # Get request details
    requests_result = get_user_requests(session.get('uid'))
    user_request = None
    
    if requests_result['success']:
        for req in requests_result['requests']:
            if req['id'] == request_id:
                user_request = req
                break
    
    # Get donations for this request
    donations_result = get_request_donations(request_id)
    donations = donations_result['donations'] if donations_result['success'] else []
    
    return render_template('request_details.html', request=user_request, donations=donations)

@people_bp.route('/update-location', methods=['POST'])
@login_required
def update_location():
    try:
        uid = session.get('uid')
        data = request.get_json()
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        address = data.get('address')
        
        result = update_user_location(uid, latitude, longitude, address)
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in update_location: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500