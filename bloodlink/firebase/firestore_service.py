from firebase.firebase_config import get_db
from datetime import datetime
import uuid

def now():
    return datetime.utcnow().isoformat()


def create_blood_request(uid, blood_type, units, location, special_requirements=''):
    """Create a new blood request"""
    try:
        db = get_db()
        request_id = str(uuid.uuid4())

        request_data = {
            'requester_uid': uid,
            'blood_type': blood_type,
            'units': int(units),
            'location': location,
            'special_requirements': special_requirements,
            'status': 'pending',
            'created_at': now(),
            'fulfilled_by': None,
            'fulfilled_at': None
        }

        db.child('blood_requests').child(request_id).set(request_data)

        # Update user request count
        user_ref = db.child('users').child(uid)
        user = user_ref.get() or {}
        user_ref.update({
            'requests': user.get('requests', 0) + 1
        })

        return {'success': True, 'request_id': request_id}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_pending_requests(user_location=None, max_distance_km=50):
    """Get all pending blood requests with slot availability"""
    try:
        db = get_db()
        requests = db.child('blood_requests').get() or {}
        donations = db.child('donations').get() or {}

        result = []

        for rid, r in requests.items():
            if r.get('status') != 'pending':
                continue

            # Count filled slots
            filled = sum(1 for d in donations.values() if d.get('request_id') == rid)
            slots_available = r.get('units', 0) - filled

            if slots_available > 0:
                r['id'] = rid
                r['slots_filled'] = filled
                r['slots_available'] = slots_available
                result.append(r)

        return {'success': True, 'requests': result}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def accept_donation_slot(request_id, donor_uid, donation_date, donation_time):
    """Accept a donation slot (1 unit only)"""
    try:
        db = get_db()

        # Get the request
        request = db.child('blood_requests').child(request_id).get()
        if not request:
            return {'success': False, 'error': 'Request not found'}

        # Check existing donations
        donations = db.child('donations').get() or {}
        existing = [d for d in donations.values() if d.get('request_id') == request_id]

        units_needed = request.get('units', 0)

        if len(existing) >= units_needed:
            return {'success': False, 'error': 'All slots filled'}

        # Check if donor already accepted
        if any(d.get('donor_uid') == donor_uid for d in existing):
            return {'success': False, 'error': 'You already accepted this request'}

        # Generate verification code
        import random
        verification_code = str(random.randint(1000, 9999))
        donation_id = str(uuid.uuid4())

        donation_data = {
            'request_id': request_id,
            'donor_uid': donor_uid,
            'requester_uid': request.get('requester_uid'),
            'blood_type': request.get('blood_type'),
            'donation_date': donation_date,
            'donation_time': donation_time,
            'verification_code': verification_code,
            'status': 'pending',
            'accepted_at': now(),
            'verified_at': None,
            'location': request.get('location')
        }

        db.child('donations').child(donation_id).set(donation_data)

        # Update request status if all slots filled
        total_accepted = len(existing) + 1
        if total_accepted >= units_needed:
            db.child('blood_requests').child(request_id).update({'status': 'all_slots_filled'})

        return {
            'success': True,
            'verification_code': verification_code,
            'donation_id': donation_id,
            'slots_remaining': units_needed - total_accepted
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def verify_donation(request_id, verification_code):
    """Verify donation with 4-digit code and award credits"""
    try:
        db = get_db()
        donations = db.child('donations').get() or {}

        # Find matching donation
        for did, d in donations.items():
            if d.get('request_id') == request_id and d.get('verification_code') == verification_code:
                if d.get('status') == 'completed':
                    return {'success': False, 'error': 'Already verified'}

                # Update donation status
                db.child('donations').child(did).update({
                    'status': 'completed',
                    'verified_at': now()
                })

                # Award credits
                donor_uid = d['donor_uid']
                user_ref = db.child('users').child(donor_uid)
                user = user_ref.get() or {}

                user_ref.update({
                    'blood_credits': user.get('blood_credits', 0) + 100,
                    'donations': user.get('donations', 0) + 1
                })

                # Check if all donations completed
                all_donations = db.child('donations').get() or {}
                request_donations = [v for v in all_donations.values() if v.get('request_id') == request_id]
                all_completed = all(d.get('status') == 'completed' for d in request_donations)

                if all_completed:
                    db.child('blood_requests').child(request_id).update({
                        'status': 'fulfilled',
                        'fulfilled_at': now()
                    })

                return {'success': True, 'donor_uid': donor_uid}

        return {'success': False, 'error': 'Invalid verification code'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_user_requests(uid):
    """Get all requests made by a user"""
    try:
        db = get_db()
        requests = db.child('blood_requests').get() or {}

        result = []
        for rid, r in requests.items():
            if r.get('requester_uid') == uid:
                r['id'] = rid
                result.append(r)

        return {'success': True, 'requests': result}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_user_donations(uid):
    """Get all donations made by a user"""
    try:
        db = get_db()
        donations = db.child('donations').get() or {}

        result = []
        for did, d in donations.items():
            if d.get('donor_uid') == uid:
                d['id'] = did
                result.append(d)

        return {'success': True, 'donations': result}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_request_donations(request_id):
    """Get all donations for a specific request"""
    try:
        db = get_db()
        donations = db.child('donations').get() or {}

        result = []
        for donation_id, d in donations.items():
            if d.get('request_id') == request_id:
                d['id'] = donation_id

                # Get donor name
                donor = db.child('users').child(d['donor_uid']).get()
                d['donor_name'] = donor.get('name', 'Anonymous') if donor else 'Anonymous'

                result.append(d)

        return {'success': True, 'donations': result}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def update_user_location(uid, latitude, longitude, address):
    """Update user's location"""
    try:
        db = get_db()
        db.child('users').child(uid).update({
            'location': {
                'latitude': latitude,
                'longitude': longitude,
                'address': address,
                'updated_at': now()
            }
        })

        return {'success': True}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def create_hospital_request(hospital_name, location, blood_type, units, urgency='normal'):
    """Create a blood request from a hospital"""
    try:
        db = get_db()
        request_id = str(uuid.uuid4())

        request_data = {
            'hospital_name': hospital_name,
            'blood_type': blood_type,
            'units': int(units),
            'location': location,
            'urgency': urgency,
            'status': 'pending',
            'type': 'hospital',
            'created_at': now()
        }

        db.child('blood_requests').child(request_id).set(request_data)

        return {'success': True, 'request_id': request_id}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def delete_user_donation(donation_id, uid):
    """Delete a donation (only if pending)"""
    try:
        db = get_db()
        
        # Get the donation
        donation = db.child('donations').child(donation_id).get()
        
        if not donation:
            return {'success': False, 'error': 'Donation not found'}
        
        # Check if user owns this donation
        if donation.get('donor_uid') != uid:
            return {'success': False, 'error': 'Unauthorized'}
        
        # Only allow deletion if pending
        if donation.get('status') != 'pending':
            return {'success': False, 'error': 'Cannot delete completed donations'}
        
        # Delete the donation
        db.child('donations').child(donation_id).delete()
        
        # Update request status back to pending if needed
        request_id = donation.get('request_id')
        if request_id:
            db.child('blood_requests').child(request_id).update({'status': 'pending'})
        
        return {'success': True}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}