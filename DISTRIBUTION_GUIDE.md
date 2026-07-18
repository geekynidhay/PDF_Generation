# FP PDF Maker - Complete Distribution Package

## 📦 What You Have

**Three standalone executable files:**

### 1. **FP_PDF_Client.exe** (~22 MB)
- **For:** End users
- **Purpose:** Main PDF maker application
- **Share:** Send this to your users
- **Requires activation:** Yes

### 2. **FP_PDF_Server.exe** (~16 MB)
- **For:** YOU (Admin only)
- **Purpose:** Activation server (backend)
- **Keep on:** Your PC only  
- **Must be running:** When users activate

### 3. **FP_PDF_Admin.exe** (~14 MB) ⭐ NEW
- **For:** YOU (Admin only)
- **Purpose:** Desktop app to manage activation keys
- **Keep on:** Your PC only
- **Easy to use:** No web browser needed!

---

## 🚀 How to Use (Simple Steps)

### Step 1: Start the Server (You)

1. Double-click `START_SERVER.bat` OR `FP_PDF_Server.exe`
2. Console window opens and shows:
   ```
   ============================================================
   FP PDF Activation Server Starting...
   Admin Panel: http://localhost:8000/admin
   ============================================================
   ```
3. **Keep this window open!**

### Step 2: Open Admin App (You)

1. Double-click `FP_PDF_Admin.exe`
2. Desktop application opens (no browser!)
3. You'll see:
   - Form to generate activation keys
   - Table showing all generated keys
   - Status indicator (server online/offline)

**That's it! No web browser needed!**

### Step 3: Share Client with Users

1. Send `FP_PDF_Client.exe` to your users
2. User runs it
3. Activation dialog appears

### Step 4: Generate Keys (You)

When user contacts you with their machine fingerprint:

1. In `FP_PDF_Admin.exe`:
   - Enter their username (e.g., "John Doe")
   - Paste their machine fingerprint (optional)
   - Click "Generate Activation Key"
2. New key appears in text box
3. Click "Copy Activation Key"
4. Send key to user

### Step 5: User Activates

1. User enters the activation key
2. User enters their name
3. Done! Features unlocked

---

## 📂 Files in dist\ folder

```
📁 j:\IR\dist\
  ├─ FP_PDF_Client.exe       ← Send to users
  ├─ FP_PDF_Admin.exe        ← YOU use this (admin panel)
  ├─ FP_PDF_Server.exe       ← Runs in background
  └─ START_SERVER.bat        ← Easy server start
```

---

## 🎯 Quick Workflow

**Your Workflow:**
```
1. Double-click START_SERVER.bat (keep window open)
2. Double-click FP_PDF_Admin.exe (desktop app opens)
3. Wait for users to send you fingerprints
4. Generate keys in the admin app
5. Copy and send keys to users
```

**User Workflow:**
```
1. Run FP_PDF_Client.exe
2. Copy their machine fingerprint
3. Send it to you
4. Receive activation key from you
5. Enter key → Activated!
```

---

## 🖥️ Admin Desktop App Features

The `FP_PDF_Admin.exe` has:

✅ **Generate Keys Section:**
- Username input field
- Machine fingerprint input field (optional)
- Generate button
- Generated key display
- Copy to clipboard button

✅ **All Keys Table:**
- Shows all activation keys
- Live status (Active/Pending)
- Username, dates, fingerprints
- Auto-refreshes every 10 seconds
- Manual refresh button

✅ **Server Status:**
- Shows if server is online/offline
- Color-coded indicator
- Automatic connection check

---

## 💡 Why Three Files?

| File | Purpose | Who Uses |
|------|---------|----------|
| `FP_PDF_Server.exe` | Backend server that stores keys | You (runs in background) |
| `FP_PDF_Admin.exe` | Desktop app to manage keys | You (interactive GUI) |
| `FP_PDF_Client.exe` | PDF maker application | Your users |

**Think of it like:**
- **Server** = Database (stores data)
- **Admin** = Dashboard (you manage data)
- **Client** = End-user app (users create PDFs)

---

## ⚙️ Setup Instructions

### One-Time Setup:

1. Put all three .exe files in `j:\IR\dist\`
2. Create a shortcut to `START_SERVER.bat` on your desktop
3. Create a shortcut to `FP_PDF_Admin.exe` on your desktop

### Daily Use:

1. Double-click `START_SERVER.bat` (once, keep open)
2. Double-click `FP_PDF_Admin.exe` (whenever users need keys)

---

## 🛡️ Managing Users (New Features)

### Revoking Access
Hostile user? Did someone leak a key? You can ban them instantly!

1. Open `FP_PDF_Admin.exe`
2. Select the user in the table
3. Click the **Red "Revoke Selected Key" Button**
4. Confirm "Yes"
5. **Result:**
   - User's status becomes "Inactive"
   - Next time they open the app, it will **lock immediately**
   - Their license file is deleted automatically

### Monitoring Users
The Admin table now shows extra details:
- **Client IP:** See the IP address of the computer using the software
- **Fingerprint:** Ensure they haven't moved to a new machine
- **Status:** Check if they are Active or Revoked

---

## ℹ️ Client Features
Your users now have a new menu: **Activation > Activation Details**
- Shows their Username
- Shows their License Key
- Shows their IP Address
- Shows Activation Date

---

## 🛠️ Troubleshooting

### Admin app shows "Server Offline"
**Solution:**
- Make sure `FP_PDF_Server.exe` or `START_SERVER.bat` is running
- Check the console window is still open
- Server needs to run first, then admin app

### Revoked user can still use app?
**Solution:**
- The app checks status on **startup**.
- They must close and reopen the app for the ban to take effect.
- Or wait for them to restart their PC.

---

## 📧 Sample User Instructions

Send this to your users:

```
Hi,

Attached is FP_PDF_Client.exe - the FP PDF Maker software.

SETUP:
1. Save FP_PDF_Client.exe anywhere on your computer
2. Double-click to run it
3. An activation dialog appears

ACTIVATION:
1. You'll see your "Machine Fingerprint"
2. Click "Copy Machine Fingerprint to Clipboard"
3. Paste and send me the fingerprint
4. I'll send you an activation key
5. Enter the key and your name
6. Done!

After first-time activation, just double-click the .exe 
and it opens immediately - no activation needed again.

Enjoy!
```

---

## ✅ Summary

**What's Different Now:**
- ✨ No need to open web browser!
- ✨ Desktop admin app is easier to use
- ✨ Everything in one place

**Your Tools:**
1. `START_SERVER.bat` - Start this first
2. `FP_PDF_Admin.exe` - Your main tool
3. `FP_PDF_Client.exe` - Share with users

**That's it! Simple and clean!** 🎉
