"""
Settings tab UI.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QSpinBox, QCheckBox, QFileDialog, QLineEdit,
    QMessageBox
)
from PyQt6.QtCore import Qt
import os
import json

from database import Database
from database.models import ScanSession


class SettingsTab(QWidget):
    """Tab for application settings"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.settings_file = os.path.expanduser('~/.config/deduplicator/settings.json')
        self.settings = self.load_settings()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Performance settings
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout()
        
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("Scanner threads:"))
        self.thread_spin = QSpinBox()
        self.thread_spin.setMinimum(1)
        self.thread_spin.setMaximum(16)
        self.thread_spin.setValue(self.settings.get('threads', 4))
        thread_layout.addWidget(self.thread_spin)
        thread_layout.addStretch()
        perf_layout.addLayout(thread_layout)
        
        cache_layout = QHBoxLayout()
        cache_layout.addWidget(QLabel("Thumbnail cache size (MB):"))
        self.cache_spin = QSpinBox()
        self.cache_spin.setMinimum(100)
        self.cache_spin.setMaximum(5000)
        self.cache_spin.setSingleStep(100)
        self.cache_spin.setValue(self.settings.get('cache_size_mb', 500))
        cache_layout.addWidget(self.cache_spin)
        cache_layout.addStretch()
        perf_layout.addLayout(cache_layout)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        # ML Settings
        ml_group = QGroupBox("ML Categorization (Ollama)")
        ml_layout = QVBoxLayout()
        
        ollama_layout = QHBoxLayout()
        ollama_layout.addWidget(QLabel("Ollama API URL:"))
        self.ollama_url = QLineEdit()
        self.ollama_url.setText(self.settings.get('ollama_url', 'http://localhost:11434'))
        ollama_layout.addWidget(self.ollama_url)
        ml_layout.addLayout(ollama_layout)
        
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Vision model:"))
        self.model_name = QLineEdit()
        self.model_name.setText(self.settings.get('vision_model', 'llava'))
        model_layout.addWidget(self.model_name)
        ml_layout.addLayout(model_layout)
        
        ml_group.setLayout(ml_layout)
        layout.addWidget(ml_group)
        
        # Database maintenance
        db_group = QGroupBox("Database")
        db_layout = QVBoxLayout()
        
        db_info = QLabel(f"Database: {os.path.expanduser('~/.local/share/deduplicator/deduplicator.db')}")
        db_layout.addWidget(db_info)
        
        clear_btn = QPushButton("Clear Old Sessions")
        clear_btn.clicked.connect(self.clear_old_sessions)
        db_layout.addWidget(clear_btn)
        
        vacuum_btn = QPushButton("Optimize Database")
        vacuum_btn.clicked.connect(self.vacuum_database)
        db_layout.addWidget(vacuum_btn)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # Cache management
        cache_group = QGroupBox("Cache")
        cache_layout = QVBoxLayout()
        
        cache_path = os.path.expanduser('~/.cache/deduplicator')
        cache_info = QLabel(f"Cache location: {cache_path}")
        cache_layout.addWidget(cache_info)
        
        clear_cache_btn = QPushButton("Clear Thumbnail Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        cache_layout.addWidget(clear_cache_btn)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # Save button
        save_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        save_layout.addWidget(save_btn)
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        layout.addStretch()
    
    def load_settings(self):
        """Load settings from file"""
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_settings(self):
        """Save settings to file"""
        self.settings = {
            'threads': self.thread_spin.value(),
            'cache_size_mb': self.cache_spin.value(),
            'ollama_url': self.ollama_url.text(),
            'vision_model': self.model_name.text()
        }
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            QMessageBox.information(self, "Settings Saved", "Settings have been saved.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save settings: {str(e)}")
    
    def clear_old_sessions(self):
        """Clear old scan sessions from database"""
        reply = QMessageBox.question(
            self, 'Clear Sessions',
            'This will delete all old scan sessions. Continue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                session = self.db.get_session()
                # Delete all scan sessions (cascade will delete related records)
                deleted_count = session.query(ScanSession).delete()
                session.commit()
                session.close()
                QMessageBox.information(
                    self, "Cleared",
                    f"Deleted {deleted_count} scan session(s) and all related data."
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear sessions: {str(e)}")
    
    def vacuum_database(self):
        """Optimize database"""
        try:
            session = self.db.get_session()
            session.execute("VACUUM")
            session.close()
            QMessageBox.information(self, "Optimized", "Database has been optimized.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to optimize database: {str(e)}")
    
    def clear_cache(self):
        """Clear thumbnail cache"""
        import shutil
        cache_path = os.path.expanduser('~/.cache/deduplicator/thumbnails')
        
        reply = QMessageBox.question(
            self, 'Clear Cache',
            'This will delete all cached thumbnails. Continue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(cache_path):
                    shutil.rmtree(cache_path)
                    os.makedirs(cache_path)
                QMessageBox.information(self, "Cleared", "Thumbnail cache has been cleared.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear cache: {str(e)}")


def load_app_settings() -> dict:
    """Load application settings from file (standalone function for use by other modules)"""
    settings_file = os.path.expanduser('~/.config/deduplicator/settings.json')
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    # Return defaults
    return {
        'threads': 4,
        'cache_size_mb': 500,
        'ollama_url': 'http://localhost:11434',
        'vision_model': 'llava'
    }
