# Activation System - Usage Guide

## 🚀 Quick Start

### Step 1: Start the Activation Server

```bash
cd j:\IR
python activation_server.py
```

**Expected Output:**
```
Database initialized at: J:\IR\activations.db

============================================================
FP PDF Activation Server Starting...
============================================================
Database: J:\IR\activations.db
Admin Panel: http://localhost:8000/admin
API Endpoint: http://localhost:8000/activate
============================================================

 * Running on http://127.0.0.1:8000
 * Running on http://192.168.1.3:8000
```

### Step 2: Access Admin Panel

Open your web browser and go to:
```
http://localhost:8000/admin
```

You should see the **FP PDF Activation Admin Panel** with:
- Form to generate new activation keys
- Table showing all issued activation keys

### Step 3: Generate Activation Key

**For a specific machine:**
1. Have the user run `client_app.py` once
2. They will see their **Machine Fingerprint** in the activation dialog
3. User sends you this fingerprint
4. In admin panel, enter:
   - Username: `John Doe` (example)
   - Machine Fingerprint: `<paste the fingerprint>`
5. Click "Generate Activation Key"
6. Copy the generated key and send it to the user

**For any machine (universal key):**
1. In admin panel, enter:
   - Username: `John Doe` (example)
   - Machine Fingerprint: `<leave empty>`
2. Click "Generate Activation Key"
3. Copy the key and send to user

### Step 4: User Activation

When user runs `client_app.py`:
1. Activation dialog appears automatically (first run)
2. They see their Machine Fingerprint
3. They enter the activation key you provided
4. They enter their name/username
5. Client contacts server at http://127.0.0.1:8000/activate
6. If valid: **Activation successful!**
7. Features are now unlocked

### Step 5: Subsequent Runs

After successful activation:
- Activation is saved in `~/.fp_pdf_activation.json`
- App auto-activates on same machine
- No prompt on future launches
- Features immediately available

## 🔧 Configuration

### Change Server Address

Edit `client_app.py` line 23:
```python
ACTIVATION_SERVER = 'http://127.0.0.1:8000'  # Change to your server IP
```

Or set environment variable:
```bash
set FP_PDF_ACTIVATION_SERVER=http://192.168.1.10:8000
python client_app.py
```

### Server on Different PC

1. Start server on PC A:
   ```bash
   python activation_server.py
   ```

2. Note the IP address from output (e.g., `http://192.168.1.3:8000`)

3. On client PC B, set environment variable:
   ```bash
   set FP_PDF_ACTIVATION_SERVER=http://192.168.1.3:8000
   python client_app.py
   ```

## 📊 Admin Panel Features

### Generate New Key
- Enter username
- Optional: paste machine fingerprint for machine-specific key
- Click generate
- Copy the displayed activation key

### View All Keys
- Real-time table updating every 10 seconds
- Shows:
  - ID
  - Activation Key
  - Username
  - Status (Active/Pending)
  - Date Issued
  - Date Activated
  - Machine Fingerprint

### Key Status
- **Pending**: Key generated but not yet activated
- **Active**: Key successfully activated on a machine

## 🔐 Security Features

### Machine-Specific Keys
- Each key can only activate ONE specific machine
- Based on hardware fingerprint (CPU, MAC, hostname)
- Prevents key sharing across multiple PCs

### Machine Fingerprint
Generated from:
- Hostname
- MAC Address
- CPU Processor ID (Windows)
- Operating System
- Machine Architecture

### Key Validation
- Server validates key exists in database
- Checks if key is already activated
- If activated, verifies it's the same machine
- Prevents reuse on different machines

## 🐛 Troubleshooting

### Error: "Cannot connect to activation server"

**Solution:**
1. Ensure server is running: `python activation_server.py`
2. Check firewall settings
3. Verify server URL in client matches server IP
4. Test server: Open `http://localhost:8000` in browser

### Error: "Invalid activation key"

**Solution:**
1. Check key was copied correctly (including dashes)
2. Verify key exists in admin panel database
3. Key format: `XXXXX-XXXXX-XXXXX-XXXXX`

### Error: "Key already activated on another machine"

**Solution:**
- This key is machine-specific and already used
- Generate a new key for this machine
- Use the machine's fingerprint when generating

### Features still disabled after activation

**Solution:**
1. Close and reopen the application
2. Check `~/.fp_pdf_activation.json` file exists
3. Delete the file and re-activate if corrupted

## 📁 Files Created

### Server Files
- `activation_server.py` - Flask server
- `activations.db` - SQLite database
- `templates/admin.html` - Admin web interface

### Client Files
- `client_app.py` - Modified with activation enforcement
- `~/.fp_pdf_activation.json` - Stored activation (on user's PC)

## 🎯 Testing Checklist

- [x] Server starts successfully
- [x] Admin panel loads at http://localhost:8000/admin
- [ ] Generate test activation key
- [ ] Delete `~/.fp_pdf_activation.json`
- [ ] Run client_app.py
- [ ] See activation prompt with fingerprint
- [ ] Enter activation key
- [ ] Verify "Activation successful" message
- [ ] Verify features are enabled
- [ ] Restart app and verify auto-activation

## 🚨 Important Notes

1. **Keep server running**: Client needs server access to activate
2. **Backup database**: `activations.db` contains all keys
3. **Server must be accessible**: Use correct IP/port in client
4. **One activation per key**: Machine-specific keys are single-use
5. **Activation file**: Users should not delete `~/.fp_pdf_activation.json`

## 💡 Tips

- Give users universal keys for flexibility
- Use machine-specific keys for license enforcement
- Monitor admin panel to see activation status
- Keep activation keys in a secure location
- Regularly backup `activations.db` database

---

# 5. ACTIVATING OVER THE INTERNET (Different Cities)

If your Admin PC is in one city (e.g., Mumbai) and the Client is in another (e.g., Delhi), they cannot connect directly using `192.168.x.x`. You must make your server accessible via the **Public Internet**.

## Option A: Using Ngrok (Easiest / Free)
This tool creates a secure tunnel from the internet to your local PC.

### 1. Setup on Admin PC (Server)
1.  Download **ngrok** from [ngrok.com](https://ngrok.com/download).
2.  Unzip it.
3.  Open a terminal/command prompt in the ngrok folder.
4.  Run your Activation Server normally:
    ```cmd
    python activation_server.py
    ```
5.  In a **new** terminal window, run ngrok to expose port 8000:
    ```cmd
    ngrok http 8000
    ```
6.  Ngrok will show a **Forwarding URL**, looks like:
    `https://2f3a-103-24-55-12.ngrok-free.app`

### 2. Configure Client (User PC)
1.  Send this `https://...` URL to the user in Delhi.
2.  When they run the Client App, it will ask for the URL.
3.  They enter: `https://2f3a-103-24-55-12.ngrok-free.app`
4.  They enter their Activation Key.

**⚠️ Important:** If you close Ngrok or restart your PC, the URL **will change**. You will need to send the new URL to your users. For a permanent URL, see Option B.

---

## Option B: Cloud Hosting (Permanent / Professional)
For a permanent solution where the URL never changes, host the server code on a cloud provider.

### Recommended: PythonAnywhere (Free Tier Available)
1.  Create a free account at [pythonanywhere.com](https://www.pythonanywhere.com/).
2.  Go to **Web** tab -> **Add a new web app**.
3.  Select **Flask** -> **Python 3.9+**.
4.  Upload your `activation_server.py` and `activations.db`.
5.  You will get a permanent URL like:
    `http://yourusername.pythonanywhere.com`
6.  Use this URL in the Client App. It will work forever as long as the site is active.
