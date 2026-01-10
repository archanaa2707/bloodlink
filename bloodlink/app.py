from flask import Flask, render_template
from flask_cors import CORS

app = Flask(__name__)
# Set your secret key directly here
app.secret_key = 'your-secret-key-here-change-this-to-something-random'
CORS(app)

# Configure session
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize Firebase
from firebase.firebase_config import initialize_firebase
initialize_firebase()

# Register blueprints
from routes.auth import auth_bp
from routes.people import people_bp
from routes.hospital import hospital_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(people_bp, url_prefix='/people')
app.register_blueprint(hospital_bp, url_prefix='/hospital')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)