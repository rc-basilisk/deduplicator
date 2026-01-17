# File Deduplicator & Organizer

A powerful desktop application for finding duplicate files and auto-organizing your data chaos. Built for Linux (Debian/KDE) with PyQt6.

## 🌟 Features

### Duplicate Detection
- **Multi-format support**: Images, documents, videos, archives, and source code
- **Smart comparison**:
  - **Images**: Perceptual hashing (finds similar images, not just exact copies)
  - **Documents**: Text extraction + fuzzy matching (TXT, DOC, DOCX, ODT, PDF, SRT)
  - **Videos**: Frame sampling + perceptual hashing
  - **Archives**: Content hashing (ZIP, TAR, GZ, ZST, etc.)
  - **Source code**: Normalized code comparison (Python, JS, TS, Elixir, HTML, etc.)
- **Adjustable similarity threshold** (80-100%)
- **Pause/Resume support** - scan thousands of files without losing progress
- **Visual previews** with thumbnails for images and videos
- **Batch operations** - select and delete duplicates across multiple folders

### Auto-Sorting
- **Automatic categorization** into folders: images, documents, videos, archives, code, others
- **ML-powered image sub-categorization** (optional, requires Ollama):
  - Screenshots
  - Photos
  - Memes
  - Artworks
  - Anime/Manga
  - Schematics/Infographics
- **Conflict handling** - automatically renames duplicates

### Performance
- **Multi-threaded scanning** for speed
- **SQLite database** for storing results (enables pause/resume)
- **Thumbnail caching** for fast preview loading
- **Lazy loading** UI - handles massive result sets efficiently

## 📋 Requirements

- **OS**: Debian 13 (or any modern Linux with KDE)
- **Python**: 3.10+
- **Optional**: Ollama with vision model (for ML image categorization)

## 🚀 Installation

### 1. Install System Dependencies

```bash
# Install Python and Qt dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Install Tesseract for PDF OCR
sudo apt install tesseract-ocr

# Install OpenCV dependencies
sudo apt install python3-opencv libopencv-dev

# Optional: Install Ollama for ML features
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llava  # Download vision model
```

### 2. Set Up Python Virtual Environment

```bash
cd ~/deduplicator

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the app
python main.py
```

## 📖 Usage Guide

### Finding Duplicates

1. **Open the "Find Duplicates" tab**
2. **Add folders to scan**:
   - Click "Add Folder"
   - Select your messy folders (dump, misc, random, cache, etc.)
   - Toggle "Include subdirectories" if needed
3. **Select file types** to scan (images, documents, videos, etc.)
4. **Adjust similarity threshold**:
   - 100%: Exact matches only
   - 95%: Very similar (recommended for images)
   - 80%: More lenient (finds more potential duplicates)
5. **Click "Start Scan"**
   - Watch the progress bar
   - Pause/Resume anytime without losing progress
6. **View Results** when complete:
   - Browse duplicate groups
   - Preview files with thumbnails
   - Select which copies to delete
   - Batch delete selected files

### Auto-Sorting Files

1. **Open the "Auto-Sort Files" tab**
2. **Add source folders** (your messy folders)
3. **Select destination folder** (where sorted files will go)
4. **Optional**: Enable "ML image categorization"
   - Requires Ollama running
   - Will create subcategories in the images folder
5. **Click "Start Sorting"**
6. Result: Files organized into:
   ```
   destination/
   ├── images/
   │   ├── screenshots/
   │   ├── photos/
   │   ├── memes/
   │   └── ...
   ├── documents/
   ├── videos/
   ├── archives/
   ├── code/
   └── others/
   ```

### Settings

Configure performance, Ollama connection, and manage cache/database in the Settings tab.

## 🔧 Advanced Usage

### Manual ML Categorization

After auto-sorting, you can run ML categorization separately on the images folder:

```python
from utils.auto_sorter import MLImageCategorizer

categorizer = MLImageCategorizer(ollama_model='llava')
categorized = categorizer.categorize_folder('/path/to/images')
categorizer.sort_by_category(categorized, '/path/to/images')
```

### Custom Similarity Threshold per File Type

Edit the scanner initialization in `core/scanner.py` to use different thresholds:

```python
self.detectors['image'] = ImageDetector(0.95)
self.detectors['document'] = DocumentDetector(0.90)
self.detectors['code'] = CodeDetector(0.85)
```

### Batch Processing via CLI

You can also use the core modules directly in scripts:

```python
from database import Database
from core import DuplicateScanner

db = Database()
session_id = db.create_scan_session("My Scan", '["image", "document"]', 0.95)

scanner = DuplicateScanner(db, session_id, ['image', 'document'], 0.95)
scanner.scan_paths([('/path/to/folder', True)])
```

## 🗂️ Project Structure

```
deduplicator/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── database/              
│   ├── models.py          # SQLAlchemy models
│   └── __init__.py
├── core/                  # Duplicate detection engine
│   ├── base.py           # Base classes
│   ├── scanner.py        # Main scanner
│   ├── image_detector.py
│   ├── document_detector.py
│   ├── video_detector.py
│   └── archive_code_detector.py
├── utils/
│   └── auto_sorter.py    # Auto-sorting + ML categorization
└── gui/                   # PyQt6 interface
    ├── main_window.py
    ├── duplicate_finder_tab.py
    ├── auto_sorter_tab.py
    └── settings_tab.py
```

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'PyQt6'"
```bash
pip install PyQt6
```

### "Tesseract not found" (PDF OCR)
```bash
sudo apt install tesseract-ocr
```

### Ollama connection failed
```bash
# Start Ollama
ollama serve

# In another terminal, pull vision model
ollama pull llava
```

### Slow performance
- Reduce number of threads in Settings
- Increase similarity threshold (fewer comparisons)
- Process folders separately instead of all at once
- Clear thumbnail cache if it gets too large

### Database locked
- Close any other instances of the app
- Check Settings → Database → Optimize Database

## 🎯 Tips for Best Results

1. **Start with images** - they're the easiest to verify visually
2. **Use 95% threshold** for images - catches similar but not identical photos
3. **Use 100% threshold** for archives and documents initially
4. **Process in batches** - scan one dump folder at a time for large collections
5. **Keep backups** - always have a backup before mass-deleting
6. **Review before deleting** - use the preview feature to double-check

## 📝 TODO / Future Enhancements

- [ ] Results viewer window (currently shows placeholder)
- [ ] Batch selection in results (select all in group, etc.)
- [ ] Export duplicate reports to CSV
- [ ] Scheduled automatic scanning
- [ ] Integration with cloud storage
- [ ] Audio file duplicate detection
- [ ] More ML models for categorization
- [ ] Dark mode support

## 🤝 Contributing

This is a personal tool, but feel free to fork and adapt for your needs!

## 📄 License

MIT License - do whatever you want with it!

## 🙏 Credits

Built with:
- PyQt6 - GUI framework
- Pillow + imagehash - Image processing
- OpenCV - Video processing
- RapidFuzz - Text similarity
- SQLAlchemy - Database ORM
- Ollama - ML categorization

---

**Happy organizing! May your data finally be tamed.** 🎉
