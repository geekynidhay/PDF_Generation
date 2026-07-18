
# Firebase Configuration
# PLEASE UPDATE THESE VALUES WITH YOUR FIREBASE PROJECT DETAILS

# 1. For the Client App (REST API)
# Found in Firebase Console -> Project Settings -> General -> Your Apps -> Web App
FIREBASE_DATABASE_URL = "https://pdf-maker-9de2c-default-rtdb.europe-west1.firebasedatabase.app"
FIREBASE_API_KEY = "AIzaSyBbkJvCQCMV9I8VrN-DxBEB8kkQ4USiIlk"  # Not strictly needed if using open REST for read, but good to have

# 2. For the Admin App (Admin SDK)
# You must place your 'serviceAccountKey.json' file in the same directory as the admin_app.exe
# Download from: Firebase Console -> Project Settings -> Service Accounts -> Generate New Private Key
SERVICE_ACCOUNT_FILE = "serviceAccountKey.json"
