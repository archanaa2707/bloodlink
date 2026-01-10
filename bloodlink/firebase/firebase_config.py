import firebase_admin
from firebase_admin import credentials, auth, db
import os

database = None

def initialize_firebase():
    global database

    try:
        firebase_admin.get_app()
    except ValueError:
        cred_path = 'serviceAccountKey.json'

        if not os.path.exists(cred_path):
            print("serviceAccountKey.json not found")
            return None

        cred = credentials.Certificate(cred_path)

        firebase_admin.initialize_app(cred, {
    "databaseURL": "https://bloodlink-d91c7-default-rtdb.asia-southeast1.firebasedatabase.app"
        })

        print("Firebase Realtime Database initialized")

    database = db.reference()
    return database


def get_db():
    global database
    if database is None:
        database = initialize_firebase()
    return database
