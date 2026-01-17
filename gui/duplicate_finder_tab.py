"""
Duplicate finder tab UI.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QCheckBox, QGroupBox, QLabel, QProgressBar, QSpinBox,
    QFileDialog, QListWidgetItem, QMessageBox, QSplitter,
    QScrollArea, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
import json
import os

from database import Database
from core import DuplicateScanner
from .results_viewer import ResultsViewer


class ScannerThread(QThread):
    """Background thread for scanning"""
    progress = pyqtSignal(int, int, str)  # current, total, message
    status = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, scanner, paths):
        super().__init__()
        self.scanner = scanner
        self.paths = paths
    
    def run(self):
        """Run the scan"""
        self.scanner.scan_paths(
            self.paths,
            progress_callback=self.progress.emit,
            status_callback=self.status.emit
        )
        self.finished.emit()


class DuplicateFinderTab(QWidget):
    """Tab for finding duplicate files"""
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.scanner = None
        self.scanner_thread = None
        self.current_session_id = None
        self.selected_paths = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Path selection section
        path_group = QGroupBox("Scan Paths")
        path_layout = QVBoxLayout()
        
        # Path list
        path_buttons_layout = QHBoxLayout()
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.remove_folder_btn = QPushButton("Remove Selected")
        self.remove_folder_btn.clicked.connect(self.remove_folder)
        path_buttons_layout.addWidget(self.add_folder_btn)
        path_buttons_layout.addWidget(self.remove_folder_btn)
        path_buttons_layout.addStretch()
        path_layout.addLayout(path_buttons_layout)
        
        self.path_list = QListWidget()
        self.path_list.setMaximumHeight(150)
        path_layout.addWidget(self.path_list)
        
        self.include_subdirs_check = QCheckBox("Include subdirectories")
        self.include_subdirs_check.setChecked(True)
        path_layout.addWidget(self.include_subdirs_check)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # File type selection
        filetype_group = QGroupBox("File Types to Scan")
        filetype_layout = QHBoxLayout()
        
        self.image_check = QCheckBox("Images")
        self.image_check.setChecked(True)
        self.document_check = QCheckBox("Documents")
        self.document_check.setChecked(True)
        self.video_check = QCheckBox("Videos")
        self.archive_check = QCheckBox("Archives")
        self.code_check = QCheckBox("Source Code")
        
        filetype_layout.addWidget(self.image_check)
        filetype_layout.addWidget(self.document_check)
        filetype_layout.addWidget(self.video_check)
        filetype_layout.addWidget(self.archive_check)
        filetype_layout.addWidget(self.code_check)
        filetype_layout.addStretch()
        
        filetype_group.setLayout(filetype_layout)
        layout.addWidget(filetype_group)
        
        # Similarity threshold
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Similarity Threshold:"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setMinimum(0.80)
        self.threshold_spin.setMaximum(1.00)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setValue(0.95)
        self.threshold_spin.setSuffix("%")
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addStretch()
        layout.addLayout(threshold_layout)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Scan")
        self.start_btn.clicked.connect(self.start_scan)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_scan)
        self.pause_btn.setEnabled(False)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)
        self.view_results_btn = QPushButton("View Results")
        self.view_results_btn.clicked.connect(self.view_results)
        self.view_results_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.view_results_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to scan")
        self.status_label.setWordWrap(True)
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        layout.addStretch()
    
    def add_folder(self):
        """Add a folder to scan"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.path_list.addItem(folder)
    
    def remove_folder(self):
        """Remove selected folder"""
        current_item = self.path_list.currentItem()
        if current_item:
            self.path_list.takeItem(self.path_list.row(current_item))
    
    def get_selected_file_types(self):
        """Get list of selected file types"""
        types = []
        if self.image_check.isChecked():
            types.append('image')
        if self.document_check.isChecked():
            types.append('document')
        if self.video_check.isChecked():
            types.append('video')
        if self.archive_check.isChecked():
            types.append('archive')
        if self.code_check.isChecked():
            types.append('code')
        return types
    
    def start_scan(self):
        """Start the duplicate scan"""
        # Validate inputs
        if self.path_list.count() == 0:
            QMessageBox.warning(self, "No Paths", "Please add at least one folder to scan.")
            return
        
        file_types = self.get_selected_file_types()
        if not file_types:
            QMessageBox.warning(self, "No File Types", "Please select at least one file type to scan.")
            return
        
        # Collect paths
        paths = []
        include_subdirs = self.include_subdirs_check.isChecked()
        for i in range(self.path_list.count()):
            path = self.path_list.item(i).text()
            paths.append((path, include_subdirs))
        
        # Create session
        similarity = self.threshold_spin.value() / 100.0
        session_name = f"Scan {len(paths)} paths"
        self.current_session_id = self.db.create_scan_session(
            session_name,
            json.dumps(file_types),
            similarity
        )
        
        # Update DB status
        self.db.update_session_status(self.current_session_id, 'running')
        
        # Create scanner
        self.scanner = DuplicateScanner(
            self.db,
            self.current_session_id,
            file_types,
            similarity
        )
        
        # Start scanner thread
        self.scanner_thread = ScannerThread(self.scanner, paths)
        self.scanner_thread.progress.connect(self.update_progress)
        self.scanner_thread.status.connect(self.update_status)
        self.scanner_thread.finished.connect(self.scan_finished)
        self.scanner_thread.start()
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Scanning...")
    
    def pause_scan(self):
        """Pause the scan"""
        if self.scanner:
            if self.scanner.is_paused:
                self.scanner.resume()
                self.pause_btn.setText("Pause")
                self.status_label.setText("Scanning (resumed)...")
            else:
                self.scanner.pause()
                self.pause_btn.setText("Resume")
                self.status_label.setText("Scanning (paused)...")
    
    def stop_scan(self):
        """Stop the scan"""
        if self.scanner:
            self.scanner.stop()
            self.status_label.setText("Stopping scan...")
            if self.current_session_id:
                self.db.update_session_status(self.current_session_id, 'cancelled')
    
    def update_progress(self, current, total, message):
        """Update progress bar"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(min(progress, 100))  # Cap at 100%
        self.status_label.setText(message)
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.setText(message)
    
    def scan_finished(self):
        """Handle scan completion"""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.view_results_btn.setEnabled(True)
        
        if self.scanner and not self.scanner.is_stopped:
            self.progress_bar.setValue(100)
            self.status_label.setText("Scan complete!")
            if self.current_session_id:
                self.db.update_session_status(self.current_session_id, 'completed')
            QMessageBox.information(self, "Scan Complete", 
                                  "Duplicate scan completed! Click 'View Results' to see duplicates.")
        else:
            self.status_label.setText("Scan stopped")
    
    def view_results(self):
        """Open results viewer"""
        if self.current_session_id:
            viewer = ResultsViewer(self.db, self.current_session_id, self)
            viewer.exec()
