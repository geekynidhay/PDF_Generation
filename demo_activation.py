"""
Quick Demo: Simulate First-Time Client Activation
This script shows what happens when a user runs the client for the first time
"""
import hashlib
import platform
import json
from pathlib import Path

def machine_fingerprint():
    """Generate unique machine fingerprint"""
    import uuid
    import subprocess
    
    info_parts = [
        platform.node(),
        platform.machine(),
        platform.system(),
        platform.processor(),
    ]
    
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                       for elements in range(0, 2*6, 2)][::-1])
        info_parts.append(mac)
    except:
        pass
    
    try:
        if platform.system() == 'Windows':
            result = subprocess.check_output(
                ['wmic', 'cpu', 'get', 'ProcessorId'],
                stderr=subprocess.DEVNULL
            ).decode().strip().split('\n')
            if len(result) > 1:
                info_parts.append(result[1].strip())
    except:
        pass
    
    combined = '|'.join(filter(None, info_parts))
    return hashlib.sha256(combined.encode()).hexdigest()

def main():
    print("="*70)
    print("FP PDF MAKER - ACTIVATION DEMO")
    print("="*70)
    
    # Check if already activated
    activation_file = Path.home() / '.fp_pdf_activation.json'
    
    print(f"\n1. Checking for activation file...")
    print(f"   Location: {activation_file}")
    
    if activation_file.exists():
        print(f"   Status: FOUND - Already activated")
        data = json.loads(activation_file.read_text())
        print(f"   Username: {data.get('username')}")
        print(f"   Token: {data.get('token')}")
        print(f"\n   >>> SOFTWARE WOULD AUTO-ACTIVATE <<<")
    else:
        print(f"   Status: NOT FOUND - First time launch")
        print(f"\n   >>> ACTIVATION DIALOG WOULD APPEAR <<<")
    
    # Show machine fingerprint
    print(f"\n2. Machine Fingerprint:")
    fp = machine_fingerprint()
    print(f"   {fp}")
    print(f"\n   >>> User would see this in activation dialog <<<")
    print(f"   >>> User provides this to admin for machine-specific key <<<")
    
    # Simulate activation flow
    print(f"\n3. Activation Flow:")
    print(f"   Step 1: Admin generates key using fingerprint above")
    print(f"   Step 2: User enters activation key in dialog")
    print(f"   Step 3: User enters their username")
    print(f"   Step 4: Client sends to server: http://localhost:8000/activate")
    print(f"   Step 5: Server validates key and fingerprint")
    print(f"   Step 6: On success, activation saved to:")
    print(f"           {activation_file}")
    print(f"   Step 7: Features unlocked!")
    
    print(f"\n4. Testing the Flow:")
    print(f"   >> To test first-time activation:")
    print(f"      1. Delete: {activation_file}")
    print(f"      2. Run: python client_app.py")
    print(f"      3. Activation dialog will appear")
    print(f"      4. Use a key from: http://localhost:8000/admin")
    
    print(f"\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    
    print(f"\nYour Current Machine Fingerprint:")
    print(f"{fp}")
    print(f"\nUse this fingerprint when generating a key in the admin panel!")

if __name__ == "__main__":
    main()
