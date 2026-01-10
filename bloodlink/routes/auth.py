from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from firebase.auth_service import create_user, verify_user_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        age = data.get('age')
        sex = data.get('sex')
        blood_type = data.get('blood_type')
        
        # Validate inputs
        if not all([email, password, name, age, sex, blood_type]):
            flash('All fields are required', 'error')
            return render_template('signup.html')
        
        # Create user
        result = create_user(email, password, name, age, sex, blood_type)
        
        if result['success']:
            flash('Account created! Please verify your email before logging in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(f'Error: {result["error"]}', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            flash('Email and password required', 'error')
            return render_template('login.html')
        
        # Verify credentials
        result = verify_user_password(email, password)
        
        if result['success']:
            # Store user info in session
            session['uid'] = result['uid']
            session['email'] = email
            session['user_data'] = result['user_data']
            
            flash('Login successful!', 'success')
            return redirect(url_for('people.dashboard'))
        else:
            flash(f'Login failed: {result["error"]}', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))