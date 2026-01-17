"""
Results viewer window for duplicate files.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QWidget, QCheckBox, QGroupBox, QMessageBox,
    QFileDialog, QSplitter, QTextEdit, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
import os
import json
import hashlib

from database import Database


class FilePreviewWidget(QWidget):
    """Widget for previewing a file"""
    
    def __init__(self, file_path, file_type):
        super().__init__()
        self.file_path = file_path
        self.file_type = file_type
        self.init_ui()
    
    def init_ui(self):
        """Initialize the preview UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if self.file_type == 'image':
            self.show_image_preview(layout)
        elif self.file_type in ['document', 'code']:
            self.show_text_preview(layout)
        elif self.file_type == 'video':
            self.show_video_preview(layout)
        elif self.file_type == 'archive':
            self.show_archive_preview(layout)
        else:
            layout.addWidget(QLabel("Preview not available"))
    
    def show_image_preview(self, layout):
        """Show image preview"""
        try:
            img_label = QLabel()
            pixmap = QPixmap(self.file_path)
            if not pixmap.isNull():
                # Scale to reasonable size while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, 
                                             Qt.TransformationMode.SmoothTransformation)
                img_label.setPixmap(scaled_pixmap)
                img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(img_label)
            else:
                layout.addWidget(QLabel("Could not load image"))
        except Exception as e:
            layout.addWidget(QLabel(f"Error loading image: {str(e)}"))
    
    def show_text_preview(self, layout):
        """Show text file preview"""
        try:
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setMaximumHeight(300)
            
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(5000)  # First 5000 chars
                if len(content) == 5000:
                    content += "\n\n[Preview truncated...]"
                text_edit.setPlainText(content)
            
            layout.addWidget(text_edit)
        except Exception as e:
            layout.addWidget(QLabel(f"Error loading file: {str(e)}"))
    
    def show_video_preview(self, layout):
        """Show video preview (placeholder for now)"""
        info_label = QLabel(f"Video file: {os.path.basename(self.file_path)}")
        layout.addWidget(info_label)
        
        # Show file size
        try:
            size = os.path.getsize(self.file_path)
            size_mb = size / (1024 * 1024)
            layout.addWidget(QLabel(f"Size: {size_mb:.2f} MB"))
        except:
            pass
    
    def show_archive_preview(self, layout):
        """Show archive preview"""
        info_label = QLabel(f"Archive file: {os.path.basename(self.file_path)}")
        layout.addWidget(info_label)
        
        # Show file size
        try:
            size = os.path.getsize(self.file_path)
            size_mb = size / (1024 * 1024)
            layout.addWidget(QLabel(f"Size: {size_mb:.2f} MB"))
        except:
            pass


class DuplicateGroupWidget(QWidget):
    """Widget displaying a group of duplicate files"""
    
    selection_changed = pyqtSignal()
    
    def __init__(self, group_id, files, file_type, similarity):
        super().__init__()
        self.group_id = group_id
        self.files = files
        self.file_type = file_type
        self.similarity = similarity
        self.file_checkboxes = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Header with similarity info
        header_layout = QHBoxLayout()
        
        type_label = QLabel(f"📄 {self.file_type.upper()}")
        type_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(type_label)
        
        similarity_label = QLabel(f"Similarity: {self.similarity*100:.1f}%")
        similarity_label.setStyleSheet("color: #0d7ea2; font-weight: bold;")
        header_layout.addWidget(similarity_label)
        
        header_layout.addStretch()
        
        # Quick select buttons
        select_all_btn = QPushButton("Select All")
        select_all_btn.setMaximumWidth(100)
        select_all_btn.clicked.connect(self.select_all)
        header_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.setMaximumWidth(100)
        select_none_btn.clicked.connect(self.select_none)
        header_layout.addWidget(select_none_btn)
        
        keep_newest_btn = QPushButton("Keep Newest")
        keep_newest_btn.setMaximumWidth(120)
        keep_newest_btn.clicked.connect(self.keep_newest)
        header_layout.addWidget(keep_newest_btn)
        
        keep_largest_btn = QPushButton("Keep Largest")
        keep_largest_btn.setMaximumWidth(120)
        keep_largest_btn.clicked.connect(self.keep_largest)
        header_layout.addWidget(keep_largest_btn)
        
        main_layout.addLayout(header_layout)
        
        # Files in this group
        files_layout = QHBoxLayout()
        
        for file_info in self.files:
            file_widget = self.create_file_widget(file_info)
            files_layout.addWidget(file_widget)
        
        files_layout.addStretch()
        main_layout.addLayout(files_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3d3d3d;")
        main_layout.addWidget(separator)
    
    def create_file_widget(self, file_info):
        """Create widget for a single file"""
        widget = QWidget()
        widget.setMaximumWidth(450)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Checkbox for deletion
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self.selection_changed.emit)
        checkbox.setProperty('file_id', file_info['id'])
        checkbox.setProperty('file_path', file_info['path'])
        self.file_checkboxes.append(checkbox)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(checkbox)
        
        delete_label = QLabel("Mark for deletion")
        delete_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        header_layout.addWidget(delete_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # File path
        path_label = QLabel(file_info['path'])
        path_label.setWordWrap(True)
        path_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(path_label)
        
        # File info
        size_mb = file_info['size'] / (1024 * 1024)
        modified = file_info['modified'].strftime('%Y-%m-%d %H:%M:%S') if file_info['modified'] else 'Unknown'
        
        info_label = QLabel(f"Size: {size_mb:.2f} MB | Modified: {modified}")
        info_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(info_label)
        
        # Preview
        preview = FilePreviewWidget(file_info['path'], self.file_type)
        layout.addWidget(preview)
        
        # Open location button
        open_btn = QPushButton("📂 Open Location")
        open_btn.clicked.connect(lambda: self.open_file_location(file_info['path']))
        layout.addWidget(open_btn)
        
        # Style the widget
        widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        return widget
    
    def open_file_location(self, file_path):
        """Open the file's location in file manager"""
        import subprocess
        directory = os.path.dirname(file_path)
        
        try:
            # For Linux
            subprocess.Popen(['xdg-open', directory])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open location: {str(e)}")
    
    def select_all(self):
        """Select all files for deletion"""
        for cb in self.file_checkboxes:
            cb.setChecked(True)
    
    def select_none(self):
        """Deselect all files"""
        for cb in self.file_checkboxes:
            cb.setChecked(False)
    
    def keep_newest(self):
        """Select all except the newest file"""
        if not self.files:
            return
        
        # Find newest file
        newest_idx = 0
        newest_time = self.files[0]['modified']
        
        for i, f in enumerate(self.files):
            if f['modified'] and f['modified'] > newest_time:
                newest_time = f['modified']
                newest_idx = i
        
        # Select all except newest
        for i, cb in enumerate(self.file_checkboxes):
            cb.setChecked(i != newest_idx)
    
    def keep_largest(self):
        """Select all except the largest file"""
        if not self.files:
            return
        
        # Find largest file
        largest_idx = 0
        largest_size = self.files[0]['size']
        
        for i, f in enumerate(self.files):
            if f['size'] > largest_size:
                largest_size = f['size']
                largest_idx = i
        
        # Select all except largest
        for i, cb in enumerate(self.file_checkboxes):
            cb.setChecked(i != largest_idx)
    
    def get_selected_files(self):
        """Get list of files marked for deletion"""
        selected = []
        for cb in self.file_checkboxes:
            if cb.isChecked():
                selected.append({
                    'id': cb.property('file_id'),
                    'path': cb.property('file_path')
                })
        return selected


class ResultsViewer(QDialog):
    """Dialog for viewing and managing duplicate scan results"""
    
    def __init__(self, db: Database, session_id: int, parent=None):
        super().__init__(parent)
        self.db = db
        self.session_id = session_id
        self.duplicate_groups = []
        self.group_widgets = []
        self.init_ui()
        self.load_results()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Duplicate Scan Results")
        self.setMinimumSize(1400, 900)
        
        layout = QVBoxLayout(self)
        
        # Header with stats
        header_layout = QHBoxLayout()
        
        self.stats_label = QLabel("Loading results...")
        self.stats_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        header_layout.addWidget(self.stats_label)
        
        header_layout.addStretch()
        
        # Filter by file type
        header_layout.addWidget(QLabel("Filter by type:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Images", "Documents", "Videos", "Archives", "Code"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        header_layout.addWidget(self.filter_combo)
        
        layout.addLayout(header_layout)
        
        # Scroll area for results
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.results_widget)
        layout.addWidget(scroll)
        
        # Bottom actions
        actions_layout = QHBoxLayout()
        
        self.selected_count_label = QLabel("0 files selected for deletion")
        actions_layout.addWidget(self.selected_count_label)
        
        actions_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_results)
        actions_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📤 Export List")
        export_btn.clicked.connect(self.export_results)
        actions_layout.addWidget(export_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete Selected Files")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        actions_layout.addWidget(self.delete_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        actions_layout.addWidget(close_btn)
        
        layout.addLayout(actions_layout)
    
    def load_results(self):
        """Load results from database"""
        # Clear existing widgets
        for widget in self.group_widgets:
            widget.deleteLater()
        self.group_widgets.clear()
        
        # Query database for duplicate groups
        session = self.db.get_session()
        
        try:
            from database.models import DuplicateGroup, FileEntry
            groups = session.query(DuplicateGroup).filter_by(
                session_id=self.session_id
            ).all()
            
            total_groups = len(groups)
            total_files = 0
            
            for group in groups:
                files = []
                for file_entry in group.files:
                    files.append({
                        'id': file_entry.id,
                        'path': file_entry.file_path,
                        'size': file_entry.file_size,
                        'modified': file_entry.modified_time
                    })
                    total_files += 1
                
                if len(files) > 1:  # Only show groups with actual duplicates
                    group_widget = DuplicateGroupWidget(
                        group.id,
                        files,
                        group.file_type,
                        group.similarity_score
                    )
                    group_widget.selection_changed.connect(self.update_selection_count)
                    self.group_widgets.append(group_widget)
                    self.results_layout.addWidget(group_widget)
            
            # Update stats
            self.stats_label.setText(
                f"Found {total_groups} duplicate groups containing {total_files} files"
            )
            
            if total_groups == 0:
                no_results = QLabel("No duplicates found! 🎉")
                no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_results.setStyleSheet("font-size: 16px; padding: 50px;")
                self.results_layout.addWidget(no_results)
        
        finally:
            session.close()
    
    def apply_filter(self, filter_text):
        """Filter results by file type"""
        filter_map = {
            "All": None,
            "Images": "image",
            "Documents": "document",
            "Videos": "video",
            "Archives": "archive",
            "Code": "code"
        }
        
        filter_type = filter_map.get(filter_text)
        
        for widget in self.group_widgets:
            if filter_type is None or widget.file_type == filter_type:
                widget.show()
            else:
                widget.hide()
    
    def update_selection_count(self):
        """Update the count of selected files"""
        total_selected = 0
        for widget in self.group_widgets:
            total_selected += len(widget.get_selected_files())
        
        self.selected_count_label.setText(f"{total_selected} files selected for deletion")
        self.delete_btn.setEnabled(total_selected > 0)
    
    def delete_selected(self):
        """Delete files marked for deletion"""
        # Collect all selected files
        files_to_delete = []
        for widget in self.group_widgets:
            files_to_delete.extend(widget.get_selected_files())
        
        if not files_to_delete:
            QMessageBox.warning(self, "No Selection", "No files selected for deletion.")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(files_to_delete)} files?\n\n"
            "This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = 0
            failed_files = []
            
            for file_info in files_to_delete:
                try:
                    os.remove(file_info['path'])
                    deleted_count += 1
                    
                    # Update database
                    session = self.db.get_session()
                    try:
                        from database.models import FileEntry
                        file_entry = session.query(FileEntry).filter_by(
                            id=file_info['id']
                        ).first()
                        if file_entry:
                            session.delete(file_entry)
                            session.commit()
                    finally:
                        session.close()
                        
                except Exception as e:
                    failed_files.append(f"{file_info['path']}: {str(e)}")
            
            # Show results
            message = f"Successfully deleted {deleted_count} files."
            if failed_files:
                message += f"\n\nFailed to delete {len(failed_files)} files:\n"
                message += "\n".join(failed_files[:5])
                if len(failed_files) > 5:
                    message += f"\n... and {len(failed_files) - 5} more"
            
            QMessageBox.information(self, "Deletion Complete", message)
            
            # Reload results
            self.load_results()
    
    def export_results(self):
        """Export results to a text file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            "duplicate_results.txt",
            "Text Files (*.txt);;CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("Duplicate Scan Results\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for widget in self.group_widgets:
                        if widget.isVisible():
                            f.write(f"\nDuplicate Group ({widget.file_type}, {widget.similarity*100:.1f}% similar):\n")
                            f.write("-" * 80 + "\n")
                            for file_info in widget.files:
                                f.write(f"  {file_info['path']}\n")
                                f.write(f"    Size: {file_info['size'] / (1024*1024):.2f} MB\n")
                            f.write("\n")
                
                QMessageBox.information(self, "Export Complete", f"Results exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export results:\n{str(e)}")
