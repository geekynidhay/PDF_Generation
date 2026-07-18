from PIL import Image
import os
import sys

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

icons_dir = r"j:\IR\Icons"
files = [
    ("Client.png", "Client.ico"),
    ("Server.png", "Server.ico"),
    ("Admin.png", "Admin.ico")
]

print("Converting icons...")
for png_file, ico_file in files:
    png_path = os.path.join(icons_dir, png_file)
    ico_path = os.path.join(icons_dir, ico_file)
    
    if os.path.exists(png_path):
        try:
            img = Image.open(png_path)
            # Create sizes for ICO
            img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
            print(f"OK: Converted {png_file} -> {ico_file}")
        except Exception as e:
            print(f"FAIL: Failed to convert {png_file}: {e}")
    else:
        print(f"WARN: File not found: {png_file}")

print("Done!")
