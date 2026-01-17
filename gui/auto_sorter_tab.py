"""
Auto-sorter tab UI for organizing files.
"""
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QCheckBox, QGroupBox, QLabel, QProgressBar, QFileDialog,
    QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from database import Database
from utils.auto_sorter import AutoSorter, MLImageCategorizer


class SorterThread(QThread):
    """Background thread for sorting"""
    progress = pyqtSignal(int, int, str)  # current, total, filepath
    status = pyqtSignal(str)
    finished = pyqtSignal(dict)  # stats
    
    def __init__(self, sorter):
        super().__init__()
        self.sorter = sorter
    
    def run(self):
        """Run the sorting"""
        stats = self.sorter.sort_files(
            progress_callback=self.progress.emit,
            status_callback=self.status.emit
        )
        self.finished.emit(stats)


class AutoSorterTab(QWidget):
    """Tab for auto-sorting files"""

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.sorter = None
        self.sorter_thread = None
        self.init_ui()

    def cleanup_thread(self):
        """Properly clean up the sorter thread to prevent memory leaks"""
        if self.sorter_thread is not None:
            if self.sorter_thread.isRunning():
                self.sorter_thread.quit()
                self.sorter_thread.wait(5000)  # Wait up to 5 seconds
                if self.sorter_thread.isRunning():
                    self.sorter_thread.terminate()
                    self.sorter_thread.wait(1000)
            self.sorter_thread = None
            self.sorter = None
    
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Source paths section
        source_group = QGroupBox("Source Folders")
        source_layout = QVBoxLayout()
        
        source_buttons_layout = QHBoxLayout()
        self.add_source_btn = QPushButton("Add Folder")
        self.add_source_btn.clicked.connect(self.add_source)
        self.remove_source_btn = QPushButton("Remove Selected")
        self.remove_source_btn.clicked.connect(self.remove_source)
        source_buttons_layout.addWidget(self.add_source_btn)
        source_buttons_layout.addWidget(self.remove_source_btn)
        source_buttons_layout.addStretch()
        source_layout.addLayout(source_buttons_layout)
        
        self.source_list = QListWidget()
        self.source_list.setMaximumHeight(150)
        source_layout.addWidget(self.source_list)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Destination section
        dest_group = QGroupBox("Destination Folder")
        dest_layout = QVBoxLayout()
        
        dest_select_layout = QHBoxLayout()
        self.dest_path = QLineEdit()
        self.dest_path.setPlaceholderText("Select destination folder...")
        self.dest_btn = QPushButton("Browse")
        self.dest_btn.clicked.connect(self.select_destination)
        dest_select_layout.addWidget(self.dest_path)
        dest_select_layout.addWidget(self.dest_btn)
        dest_layout.addLayout(dest_select_layout)
        
        dest_group.setLayout(dest_layout)
        layout.addWidget(dest_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.ml_categorize_check = QCheckBox("Use ML for image categorization (requires Ollama)")
        self.ml_categorize_check.setToolTip(
            "Enable this to automatically categorize images into subcategories like "
            "screenshots, photos, memes, artworks, etc. Requires Ollama to be running."
        )
        options_layout.addWidget(self.ml_categorize_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_sort_btn = QPushButton("Start Sorting")
        self.start_sort_btn.clicked.connect(self.start_sorting)
        control_layout.addWidget(self.start_sort_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to sort")
        self.status_label.setWordWrap(True)
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        layout.addStretch()
    
    def add_source(self):
        """Add source folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_list.addItem(folder)
    
    def remove_source(self):
        """Remove selected source folder"""
        current_item = self.source_list.currentItem()
        if current_item:
            self.source_list.takeItem(self.source_list.row(current_item))
    
    def select_destination(self):
        """Select destination folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_path.setText(folder)
    
    def start_sorting(self):
        """Start the sorting process"""
        # Validate inputs
        if self.source_list.count() == 0:
            QMessageBox.warning(self, "No Sources", "Please add at least one source folder.")
            return

        if not self.dest_path.text():
            QMessageBox.warning(self, "No Destination", "Please select a destination folder.")
            return

        # Clean up any existing thread before starting new sort
        self.cleanup_thread()

        # Collect source paths
        source_paths = []
        for i in range(self.source_list.count()):
            source_paths.append(self.source_list.item(i).text())

        # Create sorter
        self.sorter = AutoSorter(source_paths, self.dest_path.text())

        # Start sorter thread
        self.sorter_thread = SorterThread(self.sorter)
        self.sorter_thread.progress.connect(self.update_progress)
        self.sorter_thread.status.connect(self.update_status)
        self.sorter_thread.finished.connect(self.sorting_finished)
        self.sorter_thread.start()
        
        # Update UI
        self.start_sort_btn.setEnabled(False)
        self.status_label.setText("Sorting files...")
    
    def update_progress(self, current, total, filepath):
        """Update progress bar"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
        self.status_label.setText(f"Processing: {filepath}")
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.setText(message)
    
    def sorting_finished(self, stats):
        """Handle sorting completion"""
        self.start_sort_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        
        message = (
            f"Sorting complete!\n\n"
            f"Total files: {stats['total']}\n"
            f"Moved: {stats['moved']}\n"
            f"Failed: {stats['failed']}"
        )
        
        if self.ml_categorize_check.isChecked():
            # Run ML categorization on images
            self.run_ml_categorization()
        else:
            QMessageBox.information(self, "Sorting Complete", message)
    
    def run_ml_categorization(self):
        """Run ML-based image categorization"""
        images_folder = self.dest_path.text() + "/images"
        
        if not os.path.exists(images_folder):
            return
        
        try:
            categorizer = MLImageCategorizer()
            self.status_label.setText("Running ML categorization on images...")
            
            categorized = categorizer.categorize_folder(
                images_folder,
                progress_callback=lambda cur, tot, path: self.update_progress(cur, tot, path)
            )
            
            categorizer.sort_by_category(categorized, images_folder)
            
            self.status_label.setText("ML categorization complete!")
            QMessageBox.information(
                self, "Complete", 
                "Sorting and ML categorization complete!"
            )
        except Exception as e:
            QMessageBox.warning(
                self, "ML Error",
                f"ML categorization failed: {str(e)}\n\n"
                "Make sure Ollama is running with a vision model (e.g., llava)"
            )
