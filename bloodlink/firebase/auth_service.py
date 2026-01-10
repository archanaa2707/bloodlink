from firebase_admin import auth
from firebase.firebase_config import get_db
from datetime import datetime


def create_user(email, password, name, age, sex, blood_type):
    """Create user in Firebase Auth + Realtime Database"""
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )

        db = get_db()

        user_data = {
            "uid": user.uid,
            "email": email,
            "name": name,
            "age": age,
            "sex": sex,
            "blood_type": blood_type,
            "email_verified": False,
            "blood_credits": 0,
            "donations": 0,
            "requests": 0,
            "location": None,
            "created_at": datetime.utcnow().isoformat()
        }

        db.child("users").child(user.uid).set(user_data)

        verification_link = auth.generate_email_verification_link(email)

        return {
            "success": True,
            "uid": user.uid,
            "verification_link": verification_link
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def verify_user_password(email, password):
    """Simplified demo verification"""
    try:
        user = auth.get_user_by_email(email)

        db = get_db()
        user_data = db.child("users").child(user.uid).get()

        if not user_data:
            return {"success": False, "error": "User data not found"}

        return {
            "success": True,
            "uid": user.uid,
            "email_verified": user.email_verified,
            "user_data": user_data
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_user_data(uid):
    """Get user data from Realtime Database"""
    try:
        db = get_db()
        user_data = db.child("users").child(uid).get()

        if user_data:
            return {"success": True, "data": user_data}
        else:
            return {"success": False, "error": "User not found"}

    except Exception as e:
        return {"success": False, "error": str(e)}
