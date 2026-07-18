# FP PDF Maker - Activation System

## Quick Start Guide

### For Admin (You)

1. **Start the Activation Server**
   ```bash
   cd j:\IR
   python activation_server.py
   ```

2. **Access Admin Panel**
   - Open browser: **http://localhost:8000/admin**
   - (Note: Don't use just `localhost:8000` - that shows JSON API status)

3. **Generate Activation Keys**
   - User sends you their Machine Fingerprint
   - Enter their username and the fingerprint in the admin panel
   - Click "Generate Activation Key"
   - Copy the key and send it to the user

### For Users

1. **Run the Application**
   ```bash
   python client_app.py
   ```

2. **First Time Launch**
   - Activation dialog appears automatically
   - Click "Copy Machine Fingerprint to Clipboard"
   - Send the fingerprint to admin (via email, chat, etc.)
   - Wait for admin to provide activation key
   - Enter the activation key when prompted
   - Enter your name/username
   - Done! Features unlocked

3. **Subsequent Launches**
   - App auto-activates
   - No prompt shown
   - Features immediately available

## Important URLs

- **Admin Panel:** http://localhost:8000/admin
- **API Status:** http://localhost:8000
- **Activation Endpoint:** http://localhost:8000/activate

## Files

- `activation_server.py` - Server (keep running)
- `client_app.py` - Main application
- `activations.db` - Database (backup regularly)
- `ACTIVATION_GUIDE.md` - Detailed guide
- `test_activation.py` - Test all features

## Troubleshooting

**Issue:** Admin panel shows JSON instead of web interface
**Solution:** Navigate to `http://localhost:8000/admin` (with `/admin`)

**Issue:** User can't copy machine fingerprint
**Solution:** Updated! Now has a "Copy to Clipboard" button in the activation dialog

**Issue:** Server not running
**Solution:** Run `python activation_server.py` in the j:\IR directory
