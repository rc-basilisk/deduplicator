"""
Main application window with tabs for different features.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QApplication, QMessageBox, QSplashScreen, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QIcon
import sys

from database import Database
from .duplicate_finder_tab import DuplicateFinderTab
from .auto_sorter_tab import AutoSorterTab
from .settings_tab import SettingsTab
from .themes import ThemeManager


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.theme_manager = ThemeManager()
        self.init_ui()
        self.apply_theme()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('File Deduplicator & Organizer')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add header with theme toggle
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel('File Deduplicator & Organizer')
        title_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.theme_toggle_btn = QPushButton('☀️ Light Mode')
        self.theme_toggle_btn.setFixedWidth(140)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_toggle_btn)
        
        layout.addWidget(header)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Add tabs
        self.duplicate_finder = DuplicateFinderTab(self.db)
        self.auto_sorter = AutoSorterTab(self.db)
        self.settings = SettingsTab(self.db)
        
        self.tabs.addTab(self.duplicate_finder, "🔍 Find Duplicates")
        self.tabs.addTab(self.auto_sorter, "📁 Auto-Sort Files")
        self.tabs.addTab(self.settings, "⚙️ Settings")
    
    def apply_theme(self):
        """Apply current theme to the application"""
        stylesheet = self.theme_manager.get_theme(self.theme_manager.current_theme)
        self.setStyleSheet(stylesheet)
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.theme_manager.toggle_theme()
        self.apply_theme()
        
        # Update button text
        if self.theme_manager.current_theme == 'dark':
            self.theme_toggle_btn.setText('☀️ Light Mode')
        else:
            self.theme_toggle_btn.setText('🌙 Dark Mode')
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Check if any scans are running
        if hasattr(self.duplicate_finder, 'scanner_thread') and \
           self.duplicate_finder.scanner_thread and \
           self.duplicate_finder.scanner_thread.isRunning():
            reply = QMessageBox.question(
                self, 'Scan in Progress',
                'A scan is currently running. Stop it and quit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.duplicate_finder.stop_scan()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName('File Deduplicator')
    app.setOrganizationName('Deduplicator')
    
    # Set application style to Breeze if available
    app.setStyle('Breeze')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
