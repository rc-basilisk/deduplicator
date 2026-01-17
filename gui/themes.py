"""
Theme management for the application.
"""

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

QTabWidget::pane {
    border: 1px solid #3d3d3d;
    background-color: #252525;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #252525;
    border-bottom-color: #252525;
}

QTabBar::tab:hover:!selected {
    background-color: #333333;
}

QPushButton {
    background-color: #0d7ea2;
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 500;
    min-height: 30px;
}

QPushButton:hover {
    background-color: #0e96c7;
}

QPushButton:pressed {
    background-color: #0a5f7d;
}

QPushButton:disabled {
    background-color: #3d3d3d;
    color: #6d6d6d;
}

QListWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #0d7ea2;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #2d2d2d;
}

QScrollArea {
    background-color: #1e1e1e;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
}

QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #4d4d4d;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5d5d5d;
}

QScrollBar:horizontal {
    background-color: #2d2d2d;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #4d4d4d;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5d5d5d;
}

QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #4d4d4d;
    border-radius: 4px;
    background-color: #2d2d2d;
}

QCheckBox::indicator:checked {
    background-color: #0d7ea2;
    border-color: #0d7ea2;
    image: url(none);
}

QCheckBox::indicator:hover {
    border-color: #0e96c7;
}

QLabel {
    color: #e0e0e0;
}

QProgressBar {
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    text-align: center;
    background-color: #2d2d2d;
    color: #e0e0e0;
    height: 24px;
}

QProgressBar::chunk {
    background-color: #0d7ea2;
    border-radius: 5px;
}

QLineEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 8px;
}

QLineEdit:focus {
    border-color: #0d7ea2;
}

QComboBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 8px;
}

QComboBox:hover {
    border-color: #0d7ea2;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #e0e0e0;
    selection-background-color: #0d7ea2;
    border: 1px solid #3d3d3d;
}

QSpinBox, QDoubleSpinBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 6px;
}

QGroupBox {
    color: #e0e0e0;
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}

QTextEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 8px;
}

QToolTip {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #0d7ea2;
    padding: 4px;
}

/* Specific styling for duplicate results */
.duplicate-item {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 12px;
}

.duplicate-item:hover {
    background-color: #333333;
    border-color: #0d7ea2;
}
"""

LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #ffffff;
    color: #1e1e1e;
}

QTabWidget::pane {
    border: 1px solid #dcdcdc;
    background-color: #fafafa;
}

QTabBar::tab {
    background-color: #f0f0f0;
    color: #1e1e1e;
    border: 1px solid #dcdcdc;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #fafafa;
    border-bottom-color: #fafafa;
}

QTabBar::tab:hover:!selected {
    background-color: #e8e8e8;
}

QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 500;
    min-height: 30px;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #e0e0e0;
    color: #9e9e9e;
}

QListWidget {
    background-color: #ffffff;
    color: #1e1e1e;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #f0f0f0;
}

QScrollArea {
    background-color: #ffffff;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
}

QScrollBar:vertical {
    background-color: #f0f0f0;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

QScrollBar:horizontal {
    background-color: #f0f0f0;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #c0c0c0;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #a0a0a0;
}

QCheckBox {
    color: #1e1e1e;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #c0c0c0;
    border-radius: 4px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

QCheckBox::indicator:hover {
    border-color: #106ebe;
}

QLabel {
    color: #1e1e1e;
}

QProgressBar {
    border: 1px solid #dcdcdc;
    border-radius: 6px;
    text-align: center;
    background-color: #f0f0f0;
    color: #1e1e1e;
    height: 24px;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 5px;
}

QLineEdit {
    background-color: #ffffff;
    color: #1e1e1e;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    padding: 8px;
}

QLineEdit:focus {
    border-color: #0078d4;
}

QComboBox {
    background-color: #ffffff;
    color: #1e1e1e;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    padding: 8px;
}

QComboBox:hover {
    border-color: #0078d4;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1e1e1e;
    selection-background-color: #0078d4;
    border: 1px solid #dcdcdc;
}

QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #1e1e1e;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    padding: 6px;
}

QGroupBox {
    color: #1e1e1e;
    border: 2px solid #dcdcdc;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}

QTextEdit {
    background-color: #ffffff;
    color: #1e1e1e;
    border: 1px solid #dcdcdc;
    border-radius: 4px;
    padding: 8px;
}

QToolTip {
    background-color: #ffffff;
    color: #1e1e1e;
    border: 1px solid #0078d4;
    padding: 4px;
}

.duplicate-item {
    background-color: #fafafa;
    border: 1px solid #dcdcdc;
    border-radius: 6px;
    padding: 12px;
}

.duplicate-item:hover {
    background-color: #f0f0f0;
    border-color: #0078d4;
}
"""


class ThemeManager:
    """Manages application theming"""
    
    def __init__(self):
        self.current_theme = 'dark'
    
    def get_theme(self, theme_name='dark'):
        """Get stylesheet for the specified theme"""
        if theme_name == 'dark':
            return DARK_THEME
        else:
            return LIGHT_THEME
    
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        return self.get_theme(self.current_theme)
