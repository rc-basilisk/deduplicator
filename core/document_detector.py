"""
Document duplicate detector using text extraction and comparison.
"""
import os
from typing import Optional
from collections import OrderedDict
import hashlib
from rapidfuzz import fuzz
from .base import BaseDetector


class BoundedCache:
    """A simple bounded LRU-style cache using OrderedDict"""

    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self._cache: OrderedDict = OrderedDict()

    def get(self, key):
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, key, value):
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.maxsize:
                # Remove oldest item
                self._cache.popitem(last=False)
        self._cache[key] = value

    def __contains__(self, key):
        return key in self._cache

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from odf import text, teletype
    from odf.opendocument import load as odf_load
    ODF_AVAILABLE = True
except ImportError:
    ODF_AVAILABLE = False

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class DocumentDetector(BaseDetector):
    """Detect duplicate documents using text extraction and fuzzy matching"""

    def __init__(self, similarity_threshold: float = 0.95):
        super().__init__(similarity_threshold)
        # Use bounded cache to prevent unbounded memory growth
        self.text_cache = BoundedCache(maxsize=1000)

    def extract_text(self, file_path: str) -> Optional[str]:
        """Extract text from various document formats"""
        cached = self.text_cache.get(file_path)
        if cached is not None:
            return cached
        
        ext = os.path.splitext(file_path)[1].lower()
        text_content = None
        
        try:
            if ext in ['.txt', '.srt', '.vtt', '.sub']:
                text_content = self._read_text_file(file_path)
            elif ext in ['.doc', '.docx'] and DOCX_AVAILABLE:
                text_content = self._extract_docx(file_path)
            elif ext == '.odt' and ODF_AVAILABLE:
                text_content = self._extract_odt(file_path)
            elif ext == '.pdf' and PDF_AVAILABLE:
                text_content = self._extract_pdf(file_path)
            
            if text_content:
                # Normalize whitespace
                text_content = ' '.join(text_content.split())
                self.text_cache.set(file_path, text_content)
            
            return text_content
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return None
    
    def _read_text_file(self, file_path: str) -> str:
        """Read plain text file"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        return ""
    
    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = docx.Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    
    def _extract_odt(self, file_path: str) -> str:
        """Extract text from ODT"""
        doc = odf_load(file_path)
        all_text = []
        for para in doc.getElementsByType(text.P):
            all_text.append(teletype.extractText(para))
        return '\n'.join(all_text)
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text_content = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
        return '\n'.join(text_content)
    
    def compute_signature(self, file_path: str) -> Optional[str]:
        """Compute hash of document text content"""
        text = self.extract_text(file_path)
        if not text or len(text.strip()) < 10:
            return None
        
        # Use hash of normalized text
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def compare_files(self, file1: str, file2: str) -> float:
        """Compare two documents using fuzzy text matching"""
        text1 = self.extract_text(file1)
        text2 = self.extract_text(file2)

        if not text1 or not text2:
            return 0.0

        # Use token sort ratio for better matching
        similarity = fuzz.token_sort_ratio(text1, text2) / 100.0
        return similarity

    def compare_signatures(self, sig1: str, sig2: str) -> float:
        """Compare document signatures. For exact hash match, returns 1.0.
        For fuzzy matching, we need the original text (via text_cache lookup)."""
        # Document signatures are SHA256 hashes, so exact match means identical content
        if sig1 == sig2:
            return 1.0
        # For fuzzy matching, we'd need the text - return 0 for different hashes
        # since prefix-based grouping should handle similar documents
        return 0.0
