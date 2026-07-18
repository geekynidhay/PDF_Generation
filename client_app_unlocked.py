import sys
import os
import re
import json
import hashlib
import platform
import requests
import datetime
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QListWidget, QMessageBox,
    QScrollArea, QFrame, QInputDialog, QSlider, QSpinBox, QComboBox
)
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QFont
from PySide6.QtCore import Qt

# Configuration
# Configuration
# Internal Config (Embedded for single-file distribution)
FIREBASE_DATABASE_URL = "https://pdf-maker-9de2c-default-rtdb.europe-west1.firebasedatabase.app"
FIREBASE_API_KEY = "AIzaSyBbkJvCQCMV9I8VrN-DxBEB8kkQ4USiIlk"

def get_db_url(path):
    """Helper to construct URL with Auth param"""
    base = f"{FIREBASE_DATABASE_URL}/{path}"
    token = get_cached_token()
    if token:
        return f"{base}?auth={token}"
    return base

_CACHED_TOKEN = None
def get_cached_token():
    global _CACHED_TOKEN
    # Simple caching strategy: if we strictly need auth, we should sign in
    # For now, we'll try to sign in if missing
    if not _CACHED_TOKEN:
        _CACHED_TOKEN = sign_in_anonymous()
    return _CACHED_TOKEN

def sign_in_anonymous():
    """Sign in anonymously to get ID Token for database access"""
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
        resp = requests.post(url, json={"returnSecureToken": True}, timeout=10)
        if resp.status_code == 200:
            return resp.json().get('idToken')
        else:
            err_msg = f"Auth failed (Code {resp.status_code}): {resp.text}"
            print(err_msg)
            # Try to show specific error to user
            try:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Authentication Error")
                msg.setInformativeText(f"Could not sign in anonymously to Firebase.\n\nDetails:\n{resp.text}")
                msg.setWindowTitle("Firebase Error")
                msg.exec()
            except:
                pass
            return None
    except Exception as e:
        print(f"Auth error: {e}")
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Connection Error")
            msg.setInformativeText(f"Could not connect to authentication server.\n\n{e}")
            msg.exec()
        except:
            pass
        return None

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.webp'}
ACTIVATION_FILE = Path.home() / '.fp_pdf_unlocked_activation.json'


def scan_image_groups(folder: Path):
    files = [p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS and p.is_file()]
    groups = {}
    # Strip trailing copy/variant indicators in any of these forms:
    #   04692101 (1)   04692101 (  1  )   04692101 - 1   04692101-1   04692101 1
    pattern = re.compile(
        r'^(.*?)'               # base name (non-greedy)
        r'[\s\-]*'              # optional spaces/dashes before suffix
        r'(?:\(\s*\d+\s*\)|'   # either:  (1) or (  1  )
        r'\d+)'                 # or plain: 1
        r'\s*$'                 # trailing spaces then end
    )
    for p in files:
        stem = p.stem.strip()
        m = pattern.match(stem)
        if m and m.group(1).strip():
            key = m.group(1).strip()
        else:
            # fallback: group by full stem (no numeric suffix found, or base would be empty)
            key = stem
        groups.setdefault(key, []).append(p)
    # sort file lists
    for k in groups:
        groups[k].sort()
    return groups


def adjust_image_brightness(pil_image: Image.Image, brightness: int) -> Image.Image:
    """Adjust brightness of a PIL Image for PDF export (optimized version)"""
    if brightness == 0:
        return pil_image
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    from PIL import ImageEnhance
    factor = 1.0 + (brightness / 100.0)
    factor = max(0.0, min(2.0, factor))
    enhancer = ImageEnhance.Brightness(pil_image)
    return enhancer.enhance(factor)


def enhance_image_sharpness(pil_image: Image.Image) -> Image.Image:
    """Sharpen fine detail (iris texture, edges) without darkening or losing original data.

    Uses PIL UnsharpMask only — no numpy, no contrast change.
    threshold=3 means smooth areas (skin, background) are left completely
    untouched; only real edges and fine detail are sharpened.
    """
    from PIL import ImageFilter

    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')

    # radius=1.0  → sharpens fine/local detail only (good for iris)
    # percent=130 → moderate strength — brings out detail without over-sharpening
    # threshold=3 → skips flat/smooth pixels entirely, preserving brightness
    return pil_image.filter(
        ImageFilter.UnsharpMask(radius=1.0, percent=130, threshold=3)
    )



def make_preview_pixmap(title: str, image_paths, width=800, height=1131, crop_top_pct=0, crop_bottom_pct=0):
    # Keep for small previews of a single group (grid of thumbnails); applies cropping
    pix = QPixmap(width, height)
    pix.fill(QColor('white'))

    painter = QPainter(pix)
    try:
        painter.setPen(QColor('black'))
        title_font = QFont('Arial', 18)
        painter.setFont(title_font)
        painter.drawText(20, 40, title)

        cols = 4
        spacing = 12
        margin = 20
        thumb_area_w = width - 2 * margin
        thumb_w = (thumb_area_w - (cols - 1) * spacing) // cols
        x0 = margin
        y = 70

        col = 0
        for p in image_paths:
            if y > height - 80:
                break
            try:
                img = QImage(str(p))
                if img.isNull():
                    continue
                # apply crop on QImage
                ih = img.height()
                top_crop = int(ih * (crop_top_pct / 100.0))
                bottom_crop = int(ih * (crop_bottom_pct / 100.0))
                new_h = ih - top_crop - bottom_crop
                if new_h > 0:
                    img = img.copy(0, top_crop, img.width(), new_h)
                qt = QPixmap.fromImage(img).scaled(thumb_w, thumb_w, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(x0 + col * (thumb_w + spacing), y, qt)
                col += 1
                if col >= cols:
                    col = 0
                    y += qt.height() + spacing
            except Exception:
                continue
    finally:
        painter.end()
    return pix


def make_combined_preview_pixmap(groups: dict, width=800, height=1131, crop_top_pct=0, crop_bottom_pct=0):
    # Create a combined preview image - group number drawn above EACH individual image
    pix = QPixmap(width, height)
    pix.fill(QColor('white'))

    painter = QPainter(pix)
    try:
        painter.setPen(QColor('black'))
        margin = 20
        spacing = 18
        cols = 4
        thumb_area_w = width - 2 * margin
        col_w = (thumb_area_w - (cols - 1) * spacing) / cols
        label_font = QFont('Arial', 9, QFont.Bold)
        label_h = 14  # pixels reserved above each image for the label

        y = 10
        for group_name in sorted(groups.keys()):
            imgs = groups[group_name]
            col = 0
            row_h = 0
            row_buf = []  # [(QPixmap, x_pos)]

            for p in imgs:
                if y > height - 80:
                    break
                img = QImage(str(p))
                if img.isNull():
                    continue
                ih = img.height()
                top_crop = int(ih * (crop_top_pct / 100.0))
                bottom_crop = int(ih * (crop_bottom_pct / 100.0))
                new_h = ih - top_crop - bottom_crop
                if new_h > 0:
                    img = img.copy(0, top_crop, img.width(), new_h)
                iw = img.width()
                ih = img.height()
                scale = min(1.0, col_w / iw)
                tw = int(iw * scale)
                th = int(ih * scale)
                qt = QPixmap.fromImage(img).scaled(tw, th, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                qx = margin + col * (col_w + spacing) + (col_w - qt.width()) / 2
                row_buf.append((qt, qx))
                if qt.height() > row_h:
                    row_h = qt.height()
                col += 1
                if col >= cols:
                    # flush row: draw label above each image, then image
                    for qt2, qx2 in row_buf:
                        painter.setFont(label_font)
                        fm = painter.fontMetrics()
                        lw = fm.horizontalAdvance(group_name)
                        lx = int(qx2 + (col_w - lw) / 2)
                        painter.drawText(lx, int(y + label_h - 2), group_name)
                        painter.drawPixmap(int(qx2), int(y + label_h), qt2)
                    y += label_h + row_h + spacing
                    row_buf = []
                    col = 0
                    row_h = 0

            # flush remaining partial row
            if row_buf:
                for qt2, qx2 in row_buf:
                    painter.setFont(label_font)
                    fm = painter.fontMetrics()
                    lw = fm.horizontalAdvance(group_name)
                    lx = int(qx2 + (col_w - lw) / 2)
                    painter.drawText(lx, int(y + label_h - 2), group_name)
                    painter.drawPixmap(int(qx2), int(y + label_h), qt2)
                y += label_h + row_h + spacing

            y += spacing
            if y > height - 80:
                break
    finally:
        painter.end()
    return pix


def create_pdf_for_group_canvas(c, group_name: str, image_paths, page_w, page_h, y, margin=36, cols=4, spacing=18, crop_top_pct=0, crop_bottom_pct=0, brightness=0, sharpen=False):
    # Draws images as a grid onto the provided canvas, with the group number
    # printed above EACH individual image. Returns the updated y position.
    x_start = margin
    label_font_size = 10
    label_height = label_font_size + 4   # a little padding below the text

    imgs_per_row = cols
    thumb_area_w = page_w - 2 * margin
    col_w = (thumb_area_w - (cols - 1) * spacing) / cols

    # If y is near top, start at top margin
    if y is None or y < margin + 40:
        y = page_h - margin

    i = 0
    while i < len(image_paths):
        row_imgs = image_paths[i:i + imgs_per_row]
        max_row_h = 0
        scaled_sizes = []
        pil_images = []
        for p in row_imgs:
            try:
                with Image.open(p) as im:
                    iw, ih = im.size
                    # apply crop in PIL
                    top_crop = int(ih * (crop_top_pct / 100.0))
                    bottom_crop = int(ih * (crop_bottom_pct / 100.0))
                    new_h = ih - top_crop - bottom_crop
                    if new_h > 0:
                        im_cropped = im.crop((0, top_crop, iw, ih - bottom_crop))
                    else:
                        im_cropped = im.copy()
                    # Apply brightness adjustment
                    im_cropped = adjust_image_brightness(im_cropped, brightness)
                    # Apply sharpness enhancement if enabled
                    if sharpen:
                        im_cropped = enhance_image_sharpness(im_cropped)
                    iw2, ih2 = im_cropped.size
                scale = min(1.0, col_w / iw2)
                draw_w = iw2 * scale
                draw_h = ih2 * scale
                scaled_sizes.append((draw_w, draw_h))
                pil_images.append(im_cropped)
                if draw_h > max_row_h:
                    max_row_h = draw_h
            except Exception:
                scaled_sizes.append((0, 0))
                pil_images.append(None)

        # Total row height = label above + image
        total_row_h = label_height + max_row_h

        # If not enough space for this row (label + image), start a new page
        if y - total_row_h < margin:
            c.showPage()
            y = page_h - margin

        # draw row: label above each image, then the image
        x = x_start
        for idx, p in enumerate(row_imgs):
            dw, dh = scaled_sizes[idx]
            img_obj = pil_images[idx]

            # Draw number label centred above the column
            c.setFont('Helvetica-Bold', label_font_size)
            label_x = x + (col_w - c.stringWidth(group_name, 'Helvetica-Bold', label_font_size)) / 2
            c.drawString(label_x, y - label_height + 2, group_name)

            if dw > 0 and dh > 0 and img_obj is not None:
                x_center = x + (col_w - dw) / 2
                from reportlab.lib.utils import ImageReader
                c.drawImage(ImageReader(img_obj), x_center, y - label_height - dh, width=dw, height=dh)

            x += col_w + spacing

        y -= total_row_h + spacing
        i += imgs_per_row

    # leave a bit of vertical gap after the group for next group
    y -= spacing
    return y


def create_pdf_all(groups: dict, doc_name: str, out_pdf_path: Path, crop_top_pct=0, crop_bottom_pct=0, brightness=0, sharpen=False):
    page_w, page_h = A4
    margin = 36
    c = canvas.Canvas(str(out_pdf_path), pagesize=A4)

    y = page_h - margin
    for group_name in sorted(groups.keys()):
        image_paths = groups[group_name]
        y = create_pdf_for_group_canvas(c, group_name, image_paths, page_w, page_h, y, margin=margin, crop_top_pct=crop_top_pct, crop_bottom_pct=crop_bottom_pct, brightness=brightness, sharpen=sharpen)
        # if after drawing a group the y is too small for another header, start a new page
        if y < margin + 60:
            c.showPage()
            y = page_h - margin

    c.save()


class PDFMakerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FP PDF - Image to PDF (Firebase Edition)')
        self.resize(1000, 700)

        self.groups = {}
        self.current_folder = None
        self.export_folder = None
        self.preview_pixmap = None
        self.activated = False
        self.activation_info = {}
        self.brightness_value = 0  # -100 to +100, 0 = normal
        self.sharpen_enabled = False  # Sharpness enhancement toggle

        v = QVBoxLayout(self)

        # Document name first (required)
        doc_h = QHBoxLayout()
        doc_h.addWidget(QLabel('Document name (required):'))
        self.doc_name_edit = QLineEdit()
        doc_h.addWidget(self.doc_name_edit)
        v.addLayout(doc_h)
        
        # Menu bar for activation settings
        menu_h = QHBoxLayout()
        menu_h.addStretch()
        
        activation_btn = QPushButton("Activation Details")
        activation_btn.setStyleSheet("background-color: #ffa000; color: white; border-radius: 4px; padding: 5px;")
        activation_btn.clicked.connect(self.show_activation_details)
        menu_h.addWidget(activation_btn)
        
        v.insertLayout(0, menu_h)

        # Activation check on startup
        QApplication.processEvents() # Ensure UI shows up before blocking check
        # Activation check moved to end of init
        QApplication.processEvents()
        
        # Select images folder
        folder_h = QHBoxLayout()
        self.select_folder_btn = QPushButton('Select Images Folder')
        self.select_folder_btn.clicked.connect(self.on_select_folder)
        folder_h.addWidget(self.select_folder_btn)

        self.select_export_btn = QPushButton('Select Export Folder')
        self.select_export_btn.clicked.connect(self.on_select_export_folder)
        folder_h.addWidget(self.select_export_btn)

        # Machine type / crop mode
        crop_h = QHBoxLayout()
        crop_h.addWidget(QLabel('Machine Type:'))
        self.machine_type_combo = QComboBox()
        self.machine_type_combo.addItem('Old Machine - Extra Space')   # index 0 -> 13% crop
        self.machine_type_combo.addItem('New Machine - No Space')       # index 1 -> 0% crop
        self.machine_type_combo.setToolTip(
            'Old Machine - Extra Space: 13% crop top & bottom\n'
            'New Machine - No Space: 0% crop'
        )
        crop_h.addWidget(self.machine_type_combo)
        self.machine_type_combo.currentIndexChanged.connect(self.on_machine_type_changed)
        crop_h.addStretch()
        
        # Brightness control
        brightness_h = QHBoxLayout()
        brightness_h.addWidget(QLabel('Brightness:'))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.setTickPosition(QSlider.TicksBelow)
        self.brightness_slider.setTickInterval(25)
        self.brightness_slider.setToolTip('Adjust brightness (-100 to +100)')
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        brightness_h.addWidget(self.brightness_slider)
        self.brightness_label = QLabel('0%')
        self.brightness_label.setMinimumWidth(50)
        brightness_h.addWidget(self.brightness_label)

        # Sharpness enhancement checkbox
        from PySide6.QtWidgets import QCheckBox
        sharpen_h = QHBoxLayout()
        self.sharpen_chk = QCheckBox('Enhance Sharpness (Iris / Fine Detail)')
        self.sharpen_chk.setToolTip(
            'Applies Unsharp Mask + Contrast boost to make fine image detail\n'
            '(e.g. iris texture) sharper and more visible in the exported PDF.'
        )
        self.sharpen_chk.setChecked(False)
        self.sharpen_chk.stateChanged.connect(self.on_sharpen_changed)
        sharpen_h.addWidget(self.sharpen_chk)
        sharpen_h.addStretch()

        v.addLayout(folder_h)
        v.addLayout(crop_h)
        v.addLayout(brightness_h)
        v.addLayout(sharpen_h)

        # Groups list and preview
        main_h = QHBoxLayout()

        left_v = QVBoxLayout()
        left_v.addWidget(QLabel('Detected groups (click to preview):'))
        self.group_list = QListWidget()
        self.group_list.itemSelectionChanged.connect(self.on_group_selected)
        left_v.addWidget(self.group_list)

        btn_h = QHBoxLayout()
        self.preview_btn = QPushButton('Generate Preview')
        self.preview_btn.clicked.connect(self.on_generate_preview)
        btn_h.addWidget(self.preview_btn)

        self.export_selected_btn = QPushButton('Export Selected')
        self.export_selected_btn.clicked.connect(self.on_export_selected)
        btn_h.addWidget(self.export_selected_btn)

        self.export_all_btn = QPushButton('Export All')
        self.export_all_btn.clicked.connect(self.on_export_all)
        btn_h.addWidget(self.export_all_btn)

        left_v.addLayout(btn_h)
        main_h.addLayout(left_v, 1)

        # Preview area
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.addWidget(QLabel('Preview:'))
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.preview_label)
        preview_layout.addWidget(scroll)
        main_h.addWidget(preview_frame, 2)

        v.addLayout(main_h)

        # Status and summary (auto-updated when folder is selected)
        self.status_label = QLabel('Checking activation status...')
        v.addWidget(self.status_label)

        self.summary_label = QLabel('')
        v.addWidget(self.summary_label)

        self.update_ui_state()
        
        # Check activation AFTER UI is fully built
        self.check_activation_on_startup()
    
    def update_ui_state(self):
        name_ok = bool(self.doc_name_edit.text().strip())
        # Disable controls until activated
        enabled = name_ok and self.activated
        self.select_folder_btn.setEnabled(enabled)
        self.preview_btn.setEnabled(bool(self.group_list.selectedItems()) and self.activated)
        self.export_selected_btn.setEnabled(bool(self.group_list.selectedItems()) and self.export_folder is not None and self.activated)
        self.export_all_btn.setEnabled(bool(self.group_list.count()) and self.export_folder is not None and self.activated)
        if not self.activated:
            self.status_label.setText('⚠️ ACTIVATION REQUIRED - Please activate to enable all features')
        else:
            # keep existing status if activated
            pass

    def on_select_folder(self):
        name = self.doc_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, 'Missing name', 'Please enter the document name first.')
            return
        folder = QFileDialog.getExistingDirectory(self, 'Select images folder')
        if not folder:
            return
        self.current_folder = Path(folder)
        self.groups = scan_image_groups(self.current_folder)
        self.group_list.clear()
        total_files = 0
        for k in sorted(self.groups.keys()):
            count = len(self.groups[k])
            total_files += count
            # show group as single entry with number of source files in parentheses
            self.group_list.addItem(f"{k} ({count} files)")
        # Summary: number of unique items (groups) and total files
        unique_count = len(self.groups)
        self.summary_label.setText(f'Unique items: {unique_count}  |  Total files: {total_files}')

        # Auto-generate combined preview for all groups and display it
        if unique_count > 0:
            crop_pct = 13 if self.machine_type_combo.currentIndex() == 0 else 0
            top_pct = crop_pct
            bottom_pct = crop_pct
            pix = make_combined_preview_pixmap(self.groups, crop_top_pct=top_pct, crop_bottom_pct=bottom_pct)
            # Apply brightness adjustment to preview
            pix = self.adjust_brightness_pixmap(pix, self.brightness_value)
            self.preview_pixmap = pix
            self.preview_label.setPixmap(pix)
            self.status_label.setText(f'Scanned {unique_count} groups from {folder} — preview generated (crop {crop_pct}%, brightness {self.brightness_value:+d}%)')
        else:
            self.status_label.setText(f'Scanned {unique_count} groups from {folder}')

        self.update_ui_state()

    def on_select_export_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select export folder')
        if not folder:
            return
        self.export_folder = Path(folder)
        self.status_label.setText(f'Export folder set to: {folder}')
        self.update_ui_state()

    # Activation helpers
    def machine_fingerprint(self):
        """Generate unique machine fingerprint from hardware info"""
        import uuid
        import subprocess
        
        # Collect system information
        info_parts = [
            platform.node(),           # Hostname
            platform.machine(),        # Machine type
            platform.system(),         # OS name
            platform.processor(),      # Processor info
        ]
        
        # Try to get MAC address (more reliable than just uuid)
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                           for elements in range(0, 2*6, 2)][::-1])
            info_parts.append(mac)
        except:
            pass
        
        # Try to get CPU serial or other hardware ID on Windows
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
        
        # Combine and hash
        combined = '|'.join(filter(None, info_parts))
        return hashlib.sha256(combined.encode()).hexdigest()

    def load_activation(self):
        try:
            if ACTIVATION_FILE.exists():
                data = json.loads(ACTIVATION_FILE.read_text())
                return data
        except Exception:
            return None
        return None

    def save_activation(self, info: dict):
        try:
            ACTIVATION_FILE.write_text(json.dumps(info))
        except Exception:
            pass

    def prompt_for_activation(self):
        """Ask for activation token and username - show machine fingerprint with copy button"""
        fp = self.machine_fingerprint()
        
        # Create custom dialog with copyable machine ID
        from PySide6.QtWidgets import QDialog, QPushButton, QTextEdit
        from PySide6.QtGui import QClipboard
        
        # Show machine fingerprint dialog with copy button
        msg_dialog = QDialog(self)
        msg_dialog.setWindowTitle('Activation Required')
        msg_dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(msg_dialog)
        
        # Info text
        info_label = QLabel(
            f'This software requires activation via Internet.\n\n'
            'Please provide your Machine Fingerprint to your administrator\n'
            'to get an activation key.'
        )
        layout.addWidget(info_label)
        
        # Machine fingerprint label
        fp_label = QLabel('<b>Your Machine Fingerprint:</b>')
        layout.addWidget(fp_label)
        
        # Machine fingerprint text box (read-only, selectable)
        fp_text = QTextEdit()
        fp_text.setPlainText(fp)
        fp_text.setReadOnly(True)
        fp_text.setMaximumHeight(80)
        fp_text.setStyleSheet('font-family: Courier; background-color: #f0f0f0;')
        layout.addWidget(fp_text)
        
        # Copy button
        copy_btn = QPushButton('📋 Copy Machine Fingerprint to Clipboard')
        def copy_fingerprint():
            clipboard = QApplication.clipboard()
            clipboard.setText(fp)
            copy_btn.setText('✓ Copied to Clipboard!')
            copy_btn.setEnabled(False)
        
        copy_btn.clicked.connect(copy_fingerprint)
        copy_btn.setStyleSheet('padding: 8px; background-color: #4CAF50; color: white; font-weight: bold;')
        layout.addWidget(copy_btn)
        
        # OK button
        ok_btn = QPushButton('Enter Key')
        ok_btn.clicked.connect(msg_dialog.accept)
        ok_btn.setStyleSheet('padding: 8px;')
        layout.addWidget(ok_btn)
        
        msg_dialog.exec()
        
        # Ask for activation token
        token, ok = QInputDialog.getText(
            self, 
            'Activation', 
            'Enter the activation key provided by your administrator:'
        )
        if not ok or not token:
            return False
            
        # Verify via Firebase REST
        try:
             # Use helper to get URL with auth token if needed
             url = get_db_url(f"activation_keys/{token}.json")
             r = requests.get(url, timeout=10)
             
             if r.status_code != 200:
                 QMessageBox.warning(self, "Error", f"Could not connect to activation server (Code {r.status_code})")
                 return False
            
             data = r.json()
             
             if not data:
                 QMessageBox.warning(self, "Invalid Key", "The activation key is invalid.")
                 return False
                 
             # Check logic
             if not data.get('is_active'):
                 QMessageBox.warning(self, "Revoked", "This activation key has been revoked.")
                 return False
                 
             db_fp = data.get('machine_fingerprint')
             
             # If fingerprint is set and matches local
             if db_fp and db_fp == fp:
                 # Success (already activated for this machine)
                 self.activation_info = {
                     'token': token,
                     'username': data.get('username'),
                     'fingerprint': fp
                 }
                 self.save_activation(self.activation_info)
                 self.activated = True
                 QMessageBox.information(self, 'Activated', f'Activation successful!\n\nWelcome, {data.get("username")}!')
                 return True
                 
             # If fingerprint is set and DOES NOT match
             elif db_fp:
                 QMessageBox.warning(self, "Access Denied", "This key is locked to a different machine.")
                 return False
                 
             # If fingerprint is NOT set (First activation)
             else:
                 # Activate it (Update fingerprint locally and remotely)
                 # Note: Real secure apps do this server-side, but per request we use direct Firebase calls.
                 
                 now = datetime.datetime.now().isoformat()
                 
                 patch_data = {
                     'machine_fingerprint': fp,
                     'date_activated': now
                     # 'ip_address': ... (requests could fetch from ipify if needed, but skipping for simplicity)
                 }
                 
                 # Use helper for patch URL too
                 requests.patch(url, json=patch_data)
                 
                 self.activation_info = {
                     'token': token,
                     'username': data.get('username'),
                     'fingerprint': fp
                 }
                 self.save_activation(self.activation_info)
                 self.activated = True
                 QMessageBox.information(self, 'Activated', f'Activation successful!\n\nWelcome, {data.get("username")}!')
                 return True

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Connection failed:\n{e}")
            return False

    def check_activation_on_startup(self):
        """Check if user has registered a username."""
        self.activation_info = self.load_activation()
        
        if self.activation_info and self.activation_info.get('username'):
            self.activated = True
            self.status_label.setText(f"Registered to: {self.activation_info.get('username')}")
        else:
            # Prompt immediately
            self.prompt_for_username()

    def prompt_for_username(self):
        """Ask for username to register/unlock."""
        import uuid
        while True:
            username, ok = QInputDialog.getText(
                self, 
                'Registration Required', 
                'Welcome! Please enter your Name/ID to unlock the application:'
            )
            if not ok:
                sys.exit(0) # Exit if cancelled
                
            if not username or not username.strip():
                continue
                
            username = username.strip()
            
            # Generate a unique token for this unlocked client
            token = f"UNLOCKED-{str(uuid.uuid4())}"
            fp = self.machine_fingerprint()
            now = datetime.datetime.now().isoformat()
            
            # Register in Firebase
            try:
                url = get_db_url(f"activation_keys/{token}.json")
                data = {
                    'username': username,
                    'machine_fingerprint': fp,
                    'date_activated': now,
                    'is_active': True,
                    'product_type': 'unlocked_client',
                    'notes': 'Auto-registered via Unlocked Client'
                }
                # Use put/patch via requests
                requests.put(url, json=data, timeout=10)
                
                # Save locally
                self.activation_info = {
                    'token': token,
                    'username': username,
                    'fingerprint': fp
                }
                self.save_activation(self.activation_info)
                
                self.activated = True
                QMessageBox.information(self, "Success", f"Thank you, {username}! Application unlocked.")
                self.status_label.setText(f"Registered to: {username}")
                self.update_ui_state()
                return True
                
            except Exception as e:
                # If connection fails, user asked for "just username and go". 
                # Should we enforce connection? "so that i can monitor it on my admin side" implies connection IS needed.
                # But "just type username and you are good to go" implies simplicity.
                # Let's assume connection is attempted but maybe allow offline username setting if fail?
                # "monitor it on my admin side" is the key requirement. Can't monitor if offline.
                # So we enforce connection for FIRST registration.
                QMessageBox.warning(self, "Connection Error", f"Could not register: {e}\n\nPlease check your internet connection.")
                continue # Retry loop

    def show_activation_details(self):
        """Show details and connection status"""
        if not self.activated:
             QMessageBox.information(self, "Reference", f"Machine Fingerprint:\n{self.machine_fingerprint()}")
             return

        username = self.activation_info.get('username', 'Unknown')
        fp = self.activation_info.get('fingerprint', 'Unknown')
        token = self.activation_info.get('token', 'Unknown')
        
        QMessageBox.information(self, "Registration Details", 
            f"Registered User: {username}\n"
            f"Machine Default: {fp}\n"
            f"Token: {token}\n\n"
            "Status: Unlocked"
        )
        
        status_msg = "Unknown"
        try:
            url = get_db_url(f"activation_keys/{token}.json")
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                data = r.json()
                if data and data.get('is_active'):
                    status_msg = "Confirmed Active"
                else:
                    status_msg = "Revoked/Invalid"
            else:
                 status_msg = f"Server Error: {r.status_code}"
        except:
            status_msg = "Offline"

        QMessageBox.information(
            self,
            'Activation Details',
            f'<b>User Name:</b> {username}<br>'
            f'<b>License Key:</b> {token}<br>'
            f'<b>Status:</b> {status_msg}<br>'
            f'<br><b>Machine Fingerprint:</b><br>{fp}'
        )

    def on_brightness_changed(self, value):
        """Handle brightness slider changes and regenerate preview"""
        self.brightness_value = value
        self.brightness_label.setText(f'{value:+d}%')
        # Regenerate preview if images are loaded
        if self.groups:
            crop_pct = 13 if self.machine_type_combo.currentIndex() == 0 else 0
            top_pct = crop_pct
            bottom_pct = crop_pct
            pix = make_combined_preview_pixmap(self.groups, crop_top_pct=top_pct, crop_bottom_pct=bottom_pct)
            # Apply brightness adjustment to preview
            pix = self.adjust_brightness_pixmap(pix, self.brightness_value)
            self.preview_pixmap = pix
            self.preview_label.setPixmap(pix)
            self.status_label.setText(f'Preview updated with brightness {value:+d}%')

    def on_machine_type_changed(self, index):
        """Regenerate preview in real-time when machine type changes."""
        if self.groups:
            crop_pct = 13 if index == 0 else 0
            pix = make_combined_preview_pixmap(self.groups, crop_top_pct=crop_pct, crop_bottom_pct=crop_pct)
            pix = self.adjust_brightness_pixmap(pix, self.brightness_value)
            self.preview_pixmap = pix
            self.preview_label.setPixmap(pix)
            label = 'Old Machine - Extra Space (13% crop)' if index == 0 else 'New Machine - No Space (0% crop)'
            self.status_label.setText(f'Machine type changed: {label}')

    def on_sharpen_changed(self, state):
        """Toggle sharpness enhancement and refresh preview."""
        self.sharpen_enabled = bool(state)
        if self.groups:
            crop_pct = 13 if self.machine_type_combo.currentIndex() == 0 else 0
            pix = make_combined_preview_pixmap(self.groups, crop_top_pct=crop_pct, crop_bottom_pct=crop_pct)
            pix = self.adjust_brightness_pixmap(pix, self.brightness_value)
            self.preview_pixmap = pix
            self.preview_label.setPixmap(pix)
            status = 'ON' if self.sharpen_enabled else 'OFF'
            self.status_label.setText(f'Sharpness enhancement: {status} — preview updated')

    def adjust_brightness_pixmap(self, pixmap: QPixmap, brightness: int) -> QPixmap:
        """Adjust brightness of a QPixmap for preview display (optimized version)"""
        if brightness == 0:
            return pixmap
        
        # Convert QPixmap to PIL Image using QBuffer (Qt's IO device)
        from PIL import ImageEnhance
        from PySide6.QtCore import QBuffer, QIODevice
        
        # Convert QPixmap to QImage
        qimage = pixmap.toImage()
        
        # Use QBuffer to save QImage as PNG bytes
        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        qimage.save(buffer, "PNG")
        buffer.close()
        
        # Get bytes and convert to PIL Image
        from io import BytesIO
        image_bytes = buffer.data().data()
        pil_image = Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Apply brightness using PIL's ImageEnhance
        factor = 1.0 + (brightness / 100.0)
        factor = max(0.0, min(2.0, factor))
        
        enhancer = ImageEnhance.Brightness(pil_image)
        adjusted_pil = enhancer.enhance(factor)
        
        # Convert back to QPixmap using QBuffer
        output_bytes = BytesIO()
        adjusted_pil.save(output_bytes, "PNG")
        output_bytes.seek(0)
        
        # Load into QPixmap
        adjusted_pixmap = QPixmap()
        adjusted_pixmap.loadFromData(output_bytes.getvalue())
        
        return adjusted_pixmap

    def on_group_selected(self):
        self.update_ui_state()

    def on_generate_preview(self):
        # Generate a preview for all groups (combined), not single image
        if not self.groups:
            QMessageBox.information(self, 'No images', 'No images found. Please select an images folder first.')
            return
        crop_pct = 13 if self.machine_type_combo.currentIndex() == 0 else 0
        top_pct = crop_pct
        bottom_pct = crop_pct
        pix = make_combined_preview_pixmap(self.groups, crop_top_pct=top_pct, crop_bottom_pct=bottom_pct)
        # Apply brightness adjustment to preview
        pix = self.adjust_brightness_pixmap(pix, self.brightness_value)
        self.preview_pixmap = pix
        self.preview_label.setPixmap(pix)
        self.status_label.setText(f'Combined preview generated for {len(self.groups)} groups (crop {crop_pct}%, brightness {self.brightness_value:+d}%)')
        self.update_ui_state()

    def on_export_selected(self):
        sel = self.group_list.selectedItems()
        if not sel or not self.export_folder:
            QMessageBox.warning(self, 'Missing', 'Select a group and an export folder first.')
            return
        item_text = sel[0].text()
        key = item_text.split(' ')[0]
        paths = self.groups.get(key, [])
        # export as single PDF named by the group key (e.g., 08956985.pdf)
        out_name = f"{key}.pdf"
        out_path = self.export_folder / out_name
        crop_pct = 13 if self.machine_type_combo.currentIndex() == 0 else 0
        top_pct = crop_pct
        bottom_pct = crop_pct
        create_pdf_all({key: paths}, key, out_path, crop_top_pct=top_pct, crop_bottom_pct=bottom_pct, brightness=self.brightness_value, sharpen=self.sharpen_enabled)
        QMessageBox.information(self, 'Exported', f'Exported {out_path} (crop {crop_pct}%, brightness {self.brightness_value:+d}%, sharpen={self.sharpen_enabled})')
        self.status_label.setText(f'Exported {out_path}')

    def on_export_all(self):
        if not self.export_folder:
            QMessageBox.warning(self, 'Missing', 'Select an export folder first.')
            return
        out_name = f"{self.doc_name_edit.text().strip()}.pdf"
        out_path = self.export_folder / out_name
        crop_pct = 13 if self.machine_type_combo.currentIndex() == 0 else 0
        top_pct = crop_pct
        bottom_pct = crop_pct
        create_pdf_all(self.groups, self.doc_name_edit.text().strip(), out_path, crop_top_pct=top_pct, crop_bottom_pct=bottom_pct, brightness=self.brightness_value, sharpen=self.sharpen_enabled)
        QMessageBox.information(self, 'Exported', f'Exported combined PDF to {out_path} (crop {crop_pct}%, brightness {self.brightness_value:+d}%, sharpen={self.sharpen_enabled})')
        self.status_label.setText(f'Exported combined PDF to {out_path}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = PDFMakerApp()
    w.show()
    sys.exit(app.exec())
