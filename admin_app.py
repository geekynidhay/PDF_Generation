"""
FP PDF Maker - Admin Desktop Application
GUI application for managing activation keys via Firebase
"""

import sys
import json
import os
import random
import string
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QHeaderView, QTextEdit, QAbstractItemView,
    QFileDialog, QDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

# Firebase Dependencies
try:
    import firebase_admin
    from firebase_admin import credentials, db
except ImportError:
    # Fallback/Error handle in main or init
    firebase_admin = None

# Configuration
# Configuration
# Internal Config (Embedded for single-file distribution)
FIREBASE_DATABASE_URL = "https://pdf-maker-9de2c-default-rtdb.europe-west1.firebasedatabase.app"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

SERVICE_ACCOUNT_FILE = resource_path("serviceAccountKey.json")


class AdminApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FP PDF Activation - Firebase Admin Panel')
        self.setGeometry(100, 100, 1300, 750)
        
        self.firebase_initialized = False
        self.generated_key = ""
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        
        # Header
        header = QLabel('🔐 FP PDF Activation - Admin Panel (Firebase)')
        header.setFont(QFont('Arial', 18, QFont.Bold))
        header.setStyleSheet('color: #ffa000; padding: 10px;') # Firebase Orange/Yellowish
        layout.addWidget(header)
        
        # Server status
        self.status_label = QLabel('Initializing Firebase connection...')
        self.status_label.setStyleSheet('padding: 5px; background-color: #f0f0f0; border-radius: 3px;')
        layout.addWidget(self.status_label)
        
        # Generate key section
        generate_group = QGroupBox('Generate New Activation Key')
        generate_group.setStyleSheet('''
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ffa000;
                border-radius: 5px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        ''')
        generate_layout = QVBoxLayout()
        
        # Username input
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel('Username / Client Name:'))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('e.g., John Doe')
        user_layout.addWidget(self.username_input)
        generate_layout.addLayout(user_layout)
        
        # Fingerprint input
        fp_layout = QHBoxLayout()
        fp_layout.addWidget(QLabel('Machine Fingerprint (Optional):'))
        self.fingerprint_input = QLineEdit()
        self.fingerprint_input.setPlaceholderText('Leave empty for universal key, or paste specific fingerprint')
        fp_layout.addWidget(self.fingerprint_input)
        generate_layout.addLayout(fp_layout)
        
        # Info label
        info_label = QLabel('💡 For machine-specific keys, ask user to run client and send their fingerprint')
        info_label.setStyleSheet('color: #666; font-style: italic; padding: 5px;')
        generate_layout.addWidget(info_label)
        
        # Generate button
        self.generate_btn = QPushButton('Generate Activation Key')
        self.generate_btn.setStyleSheet('''
            QPushButton {
                background-color: #ffa000;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ff8f00;
            }
        ''')
        self.generate_btn.clicked.connect(self.generate_key)
        self.generate_btn.setEnabled(False) # Enable only after successful init
        generate_layout.addWidget(self.generate_btn)
        
        # Generated key display
        self.key_display = QTextEdit()
        self.key_display.setReadOnly(True)
        self.key_display.setMaximumHeight(60)
        self.key_display.setStyleSheet('''
            background-color: #fff8e1;
            border: 2px dashed #ffa000;
            border-radius: 5px;
            font-family: Courier;
            font-size: 14px;
            padding: 5px;
        ''')
        self.key_display.hide()
        generate_layout.addWidget(self.key_display)
        
        # Copy button
        self.copy_btn = QPushButton('📋 Copy Activation Key')
        self.copy_btn.setStyleSheet('''
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        ''')
        self.copy_btn.clicked.connect(self.copy_key)
        self.copy_btn.hide()
        generate_layout.addWidget(self.copy_btn)
        
        generate_group.setLayout(generate_layout)
        layout.addWidget(generate_group)
        
        # Keys table section
        table_group = QGroupBox('All Activation Keys (Firebase)')
        table_group.setStyleSheet('''
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ffa000;
                border-radius: 5px;
                margin-top: 10px;
                padding: 15px;
            }
        ''')
        table_layout = QVBoxLayout()
        
        # Validation controls
        ctrl_layout = QHBoxLayout()
        
        # Refresh button
        refresh_btn = QPushButton('🔄 Refresh')
        refresh_btn.clicked.connect(self.load_keys)
        refresh_btn.setMaximumWidth(100)
        ctrl_layout.addWidget(refresh_btn)
        
        # Revoke button
        revoke_btn = QPushButton('🚫 Revoke Selected Key')
        revoke_btn.setStyleSheet('''
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #bd2130;
            }
        ''')
        revoke_btn.clicked.connect(self.revoke_key)
        ctrl_layout.addWidget(revoke_btn)
        
        ctrl_layout.addStretch()
        table_layout.addLayout(ctrl_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Activation Key', 'Username', 'Status', 
            'Date Issued', 'Date Activated', 'Machine Fingerprint', 'Client IP'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setStyleSheet('''
            QTableWidget {
                gridline-color: #d0d0d0;
            }
            QTableWidget::item {
                padding: 5px;
            }
        ''')
        table_layout.addWidget(self.table)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Initialize Firebase (delayed to let UI show)
        QTimer.singleShot(500, self.init_firebase)

    def init_firebase(self):
        """Initialize Firebase Admin SDK"""
        if not firebase_admin:
             QMessageBox.critical(self, "Missing Library", "The 'firebase_admin' library is not installed.\nPlease run: pip install firebase-admin")
             self.status_label.setText("❌ Error: Missing firebase-admin library")
             return

        # Check for service account file
        service_account_path = SERVICE_ACCOUNT_FILE
        if not os.path.exists(service_account_path):
             QMessageBox.warning(self, "Missing Configuration", 
                                 f"Could not find '{SERVICE_ACCOUNT_FILE}'.\n\n"
                                 "Please select your Firebase Admin SDK private key JSON file.")
             file_path, _ = QFileDialog.getOpenFileName(self, "Select Service Account JSON", "", "JSON Files (*.json)")
             if file_path:
                 service_account_path = file_path
             else:
                 self.status_label.setText("❌ Error: No Service Account provided")
                 return

        try:
            cred = credentials.Certificate(service_account_path)
            # Check if app already initialized
            try:
                firebase_admin.get_app()
            except ValueError:
                firebase_admin.initialize_app(cred, {
                    'databaseURL': FIREBASE_DATABASE_URL
                })
            
            self.firebase_initialized = True
            self.status_label.setText(f"✅ Connected to Firebase: {FIREBASE_DATABASE_URL}")
            self.status_label.setStyleSheet('padding: 5px; background-color: #d4edda; border-radius: 3px; color: #155724;')
            self.generate_btn.setEnabled(True)
            self.load_keys()
            
        except Exception as e:
            self.status_label.setText(f"❌ Connection Failed: {str(e)}")
            self.status_label.setStyleSheet('padding: 5px; background-color: #f8d7da; border-radius: 3px; color: #721c24;')
            self.status_label.setToolTip(str(e))
            QMessageBox.critical(self, "Firebase Error", f"Failed to initialize Firebase:\n{str(e)}")

    def generate_key(self):
        """Generate a new activation key and save to Firebase"""
        if not self.firebase_initialized:
            return

        username = self.username_input.text().strip()
        fingerprint = self.fingerprint_input.text().strip()
        
        if not username:
            QMessageBox.warning(self, 'Missing Information', 'Please enter a username!')
            return
        
        try:
            # Generate random key
            # Format: XXXXX-XXXXX-XXXXX-XXXXX
            def chunk(): return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            key = f"{chunk()}-{chunk()}-{chunk()}-{chunk()}"
            
            now = datetime.now().isoformat()
            
            data = {
                'username': username,
                'machine_fingerprint': fingerprint if fingerprint else None,
                'date_issued': now,
                'is_active': True,
                'date_activated': None,
                'ip_address': None
            }
            
            # Save to /activation_keys/{key}
            ref = db.reference(f'activation_keys/{key}')
            ref.set(data)
            
            self.generated_key = key
            
            # Show the key
            self.key_display.setPlainText(f'Activation Key:\n{key}')
            self.key_display.show()
            self.copy_btn.show()
            
            # Clear inputs
            self.username_input.clear()
            self.fingerprint_input.clear()
            
            # Refresh table
            self.load_keys()
            
            QMessageBox.information(
                self,
                'Success',
                f'Activation key generated successfully!\n\nKey: {key}\n\nClick "Copy Activation Key" to copy it.'
            )
        
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to generate key:\n{str(e)}')
    
    def copy_key(self):
        """Copy generated key to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.generated_key)
        self.copy_btn.setText('✓ Copied to Clipboard!')
        QTimer.singleShot(2000, lambda: self.copy_btn.setText('📋 Copy Activation Key'))
    
    def load_keys(self):
        """Load all activation keys from Firebase"""
        if not self.firebase_initialized:
            return
        
        try:
            ref = db.reference('activation_keys')
            data = ref.get() or {} # Returns dict of keys
            
            # Sort by date issued (descending)
            # data is dict: { "KEY-1": {...}, "KEY-2": {...} }
            keys_list = []
            for k, v in data.items():
                v['key'] = k # Ensure key is present
                keys_list.append(v)
            
            # Sort helper
            def get_date(item):
                d = item.get('date_issued', '')
                return d
            
            keys_list.sort(key=get_date, reverse=True)
            
            # Update table
            self.table.setRowCount(len(keys_list))
            
            for row, key_data in enumerate(keys_list):
                # ID (using loop index for display as Firebase doesn't have auto-increment ID like SQL)
                self.table.setItem(row, 0, QTableWidgetItem(str(len(keys_list) - row)))
                
                # Activation Key
                key_item = QTableWidgetItem(key_data.get('key', 'Unknown'))
                key_item.setFont(QFont('Courier', 9))
                self.table.setItem(row, 1, key_item)
                
                # Username
                self.table.setItem(row, 2, QTableWidgetItem(key_data.get('username', '')))
                
                # Status
                is_active = key_data.get('is_active', False)
                status_item = QTableWidgetItem('Active' if is_active else 'Revoked')
                if is_active:
                    status_item.setForeground(QColor('#28a745'))
                else:
                    status_item.setForeground(QColor('#dc3545'))
                status_item.setFont(QFont('Arial', 9, QFont.Bold))
                self.table.setItem(row, 3, status_item)
                
                # Date Issued
                issued = self.format_date(key_data.get('date_issued', ''))
                self.table.setItem(row, 4, QTableWidgetItem(issued))
                
                # Date Activated
                activated = key_data.get('date_activated')
                if not activated:
                    activated = "Not activated"
                else:
                    activated = self.format_date(activated)
                self.table.setItem(row, 5, QTableWidgetItem(activated))
                
                # Machine Fingerprint
                fp = key_data.get('machine_fingerprint')
                if not fp:
                    fp = "Universal"
                elif len(fp) > 20: 
                    fp = fp[:20] + '...'
                fp_item = QTableWidgetItem(fp)
                fp_item.setFont(QFont('Courier', 8))
                self.table.setItem(row, 6, fp_item)
                
                # Client IP
                ip = key_data.get('ip_address', '-')
                self.table.setItem(row, 7, QTableWidgetItem(ip))
        
        except Exception as e:
            # Silent fail for auto-refresh might be bad if auth fails, but okay for network blips
            print(f"Error loading keys: {e}")
    
    def revoke_key(self):
        """Revoke the selected key"""
        if not self.firebase_initialized:
            return

        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, 'Selection', 'Please select a row to revoke!')
            return
            
        row = rows[0].row()
        key = self.table.item(row, 1).text()
        username = self.table.item(row, 2).text()
        status_text = self.table.item(row, 3).text()
        
        # We can revoke even if already revoked (to ensure sync?) but usually checks status
        # if status_text != "Active": ...
        
        confirm = QMessageBox.question(
            self,
            'Confirm Revocation',
            f'Are you sure you want to REVOKE access for user:\n\n{username}\n\nKey: {key}\n\nThis will ban them from using the software!',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                # Update /activation_keys/{key}/is_active = False
                ref = db.reference(f'activation_keys/{key}')
                ref.update({'is_active': False})
                
                QMessageBox.information(self, 'Revoked', 'Key successfully revoked.')
                self.load_keys()
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Connection error: {e}')

    def format_date(self, iso_date):
        """Format ISO date to readable format"""
        try:
            dt = datetime.fromisoformat(iso_date)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return iso_date


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AdminApp()
    window.show()
    sys.exit(app.exec())
