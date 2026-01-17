"""
Base classes and utilities for file detection and duplicate finding.
"""
import os
import hashlib
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import mimetypes


class FileInfo:
    """Container for file information"""
    def __init__(self, path: str):
        self.path = path
        self.size = os.path.getsize(path)
        # Convert Unix timestamp to datetime object for SQLAlchemy
        self.modified = datetime.fromtimestamp(os.path.getmtime(path))
        self.name = os.path.basename(path)
        self.ext = os.path.splitext(path)[1].lower()
        self.mime_type = mimetypes.guess_type(path)[0]
    
    def __repr__(self):
        return f"FileInfo({self.path})"


class BaseDetector(ABC):
    """Base class for duplicate detectors"""
    
    def __init__(self, similarity_threshold: float = 0.95):
        self.similarity_threshold = similarity_threshold
    
    @abstractmethod
    def compute_signature(self, file_path: str) -> Optional[str]:
        """Compute a signature/hash for the file"""
        pass
    
    @abstractmethod
    def compare_files(self, file1: str, file2: str) -> float:
        """Compare two files and return similarity score (0.0-1.0)"""
        pass
    
    @staticmethod
    def file_hash(file_path: str, algorithm='sha256') -> str:
        """Compute file hash"""
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    
    @staticmethod
    def quick_hash(file_path: str, sample_size: int = 8192) -> str:
        """Quick hash using file start/middle/end"""
        file_size = os.path.getsize(file_path)
        hash_func = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            # Start
            hash_func.update(f.read(sample_size))
            
            # Middle
            if file_size > sample_size * 2:
                f.seek(file_size // 2)
                hash_func.update(f.read(sample_size))
            
            # End
            if file_size > sample_size:
                f.seek(-sample_size, 2)
                hash_func.update(f.read(sample_size))
        
        return hash_func.hexdigest()


class FileScanner:
    """Scans directories for files"""
    
    SUPPORTED_EXTENSIONS = {
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'},
        'document': {'.txt', '.doc', '.docx', '.odt', '.pdf', '.rtf', '.srt', '.vtt', '.sub'},
        'video': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'},
        'archive': {'.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar', '.zst'},
        'code': {'.py', '.js', '.ts', '.exs', '.html', '.css', '.jsx', '.tsx', '.vue', '.rs', '.go', '.cpp', '.c', '.h'}
    }
    
    EXCLUDE_DIRS = {
        'node_modules', '__pycache__', '.git', '.svn', 'venv', 'env',
        '.venv', 'dist', 'build', '.cache', '.pytest_cache', '.mypy_cache'
    }
    
    def __init__(self, file_types: List[str] = None):
        """
        Args:
            file_types: List of file types to scan for (e.g., ['image', 'document'])
        """
        self.file_types = file_types or list(self.SUPPORTED_EXTENSIONS.keys())
        self.extensions = set()
        for ft in self.file_types:
            self.extensions.update(self.SUPPORTED_EXTENSIONS.get(ft, set()))
    
    def scan_directory(self, path: str, include_subdirs: bool = True, 
                      progress_callback=None) -> List[FileInfo]:
        """
        Scan directory for files
        
        Args:
            path: Directory path to scan
            include_subdirs: Whether to scan subdirectories
            progress_callback: Optional callback(current_file, total_files)
        
        Returns:
            List of FileInfo objects
        """
        files = []
        total = 0
        
        if include_subdirs:
            for root, dirs, filenames in os.walk(path):
                # Exclude certain directories
                dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
                
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in self.extensions:
                        file_path = os.path.join(root, filename)
                        try:
                            files.append(FileInfo(file_path))
                            total += 1
                            if progress_callback:
                                progress_callback(file_path, total)
                        except (OSError, PermissionError):
                            continue
        else:
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path):
                        ext = os.path.splitext(item)[1].lower()
                        if ext in self.extensions:
                            try:
                                files.append(FileInfo(item_path))
                                total += 1
                                if progress_callback:
                                    progress_callback(item_path, total)
                            except (OSError, PermissionError):
                                continue
            except (OSError, PermissionError):
                pass
        
        return files
    
    def get_file_category(self, file_path: str) -> Optional[str]:
        """Determine which category a file belongs to"""
        ext = os.path.splitext(file_path)[1].lower()
        for category, extensions in self.SUPPORTED_EXTENSIONS.items():
            if ext in extensions:
                return category
        return None
