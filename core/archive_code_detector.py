"""
Archive and code file duplicate detectors.
"""
import os
from typing import Optional
import hashlib
from .base import BaseDetector
from rapidfuzz import fuzz


class ArchiveDetector(BaseDetector):
    """Detect duplicate archives using content hashing"""
    
    def compute_signature(self, file_path: str) -> Optional[str]:
        """Compute SHA256 hash of archive file"""
        try:
            return self.file_hash(file_path, 'sha256')
        except Exception as e:
            print(f"Error hashing {file_path}: {e}")
            return None
    
    def compare_files(self, file1: str, file2: str) -> float:
        """Compare archives - exact match only"""
        hash1 = self.compute_signature(file1)
        hash2 = self.compute_signature(file2)
        
        if not hash1 or not hash2:
            return 0.0
        
        return 1.0 if hash1 == hash2 else 0.0


class CodeDetector(BaseDetector):
    """Detect duplicate source code files"""
    
    def __init__(self, similarity_threshold: float = 0.95):
        super().__init__(similarity_threshold)
        self.code_cache = {}
    
    def normalize_code(self, file_path: str) -> Optional[str]:
        """Read and normalize code (remove comments, normalize whitespace)"""
        if file_path in self.code_cache:
            return self.code_cache[file_path]
        
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if not content:
                return None
            
            # Basic normalization: remove empty lines, normalize whitespace
            lines = [line.strip() for line in content.split('\n')]
            lines = [line for line in lines if line and not line.startswith(('#', '//', '/*'))]
            normalized = ' '.join(lines)
            
            self.code_cache[file_path] = normalized
            return normalized
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    def compute_signature(self, file_path: str) -> Optional[str]:
        """Compute hash of normalized code"""
        code = self.normalize_code(file_path)
        if not code:
            return None
        
        return hashlib.sha256(code.encode('utf-8')).hexdigest()
    
    def compare_files(self, file1: str, file2: str) -> float:
        """Compare code files using fuzzy matching"""
        code1 = self.normalize_code(file1)
        code2 = self.normalize_code(file2)
        
        if not code1 or not code2:
            return 0.0
        
        # Use token set ratio for code comparison
        similarity = fuzz.token_set_ratio(code1, code2) / 100.0
        return similarity
