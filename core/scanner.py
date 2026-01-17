"""
Main scanning engine that coordinates duplicate detection.
"""
import os
from typing import List, Dict, Tuple, Optional, Callable
from collections import defaultdict
from pathlib import Path

from .base import FileScanner, FileInfo
from .image_detector import ImageDetector
from .document_detector import DocumentDetector
from .video_detector import VideoDetector
from .archive_code_detector import ArchiveDetector, CodeDetector
from database.models import Database, DuplicateGroup, FileEntry


class DuplicateScanner:
    """Main scanner engine"""
    
    def __init__(self, db: Database, session_id: int, 
                 file_types: List[str], similarity_threshold: float = 0.95):
        self.db = db
        self.session_id = session_id
        self.file_types = file_types
        self.similarity_threshold = similarity_threshold
        
        # Initialize detectors
        self.detectors = {}
        if 'image' in file_types:
            self.detectors['image'] = ImageDetector(similarity_threshold)
        if 'document' in file_types:
            self.detectors['document'] = DocumentDetector(similarity_threshold)
        if 'video' in file_types:
            self.detectors['video'] = VideoDetector(similarity_threshold)
        if 'archive' in file_types:
            self.detectors['archive'] = ArchiveDetector(similarity_threshold)
        if 'code' in file_types:
            self.detectors['code'] = CodeDetector(similarity_threshold)
        
        self.scanner = FileScanner(file_types)
        self.is_paused = False
        self.is_stopped = False
    
    def scan_paths(self, paths: List[Tuple[str, bool]], 
                   progress_callback: Optional[Callable] = None,
                   status_callback: Optional[Callable] = None):
        """
        Scan multiple paths for duplicates
        
        Args:
            paths: List of (path, include_subdirs) tuples
            progress_callback: Callback(current, total, status_message)
            status_callback: Callback(status_message)
        """
        # Step 1: Collect all files (Discovery Phase)
        if status_callback:
            status_callback("📂 Phase 1/3: Discovering files...")
        
        all_files = []
        for path_idx, (path, include_subdirs) in enumerate(paths):
            if status_callback:
                status_callback(f"📂 Phase 1/3: Scanning folder {path_idx + 1}/{len(paths)}...")
            
            files = self.scanner.scan_directory(
                path, 
                include_subdirs,
                progress_callback=lambda fp, count: progress_callback(
                    int((path_idx / len(paths)) * 100),
                    100,
                    f"Discovered {len(all_files) + count} files"
                ) if progress_callback else None
            )
            all_files.extend(files)
        
        if self.is_stopped:
            return
        
        total_files = len(all_files)
        if status_callback:
            status_callback(f"✅ Found {total_files} files")
        
        if progress_callback:
            progress_callback(100, 100, f"Found {total_files} files")
        
        # Step 2: Group files by category
        files_by_category = defaultdict(list)
        for file_info in all_files:
            category = self.scanner.get_file_category(file_info.path)
            if category:
                files_by_category[category].append(file_info)
        
        # Step 3: Find duplicates for each category (Processing Phase)
        session = self.db.get_session()
        thumbnails_dir = os.path.expanduser('~/.cache/deduplicator/thumbnails')
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # Calculate total work for progress
        total_categories = len(files_by_category)
        current_category = 0
        
        for category, files in files_by_category.items():
            if self.is_stopped:
                break
            
            current_category += 1
            category_display = category.title() + 's'
            
            if status_callback:
                status_callback(f"🔍 Phase 2/3: Analyzing {category_display} ({len(files)} files)...")
            
            detector = self.detectors.get(category)
            if not detector:
                continue
            
            # Find duplicates
            duplicates = self._find_duplicates(
                files, detector, category,
                lambda cur, tot: progress_callback(
                    int(((current_category - 1) / total_categories + (cur / tot / total_categories)) * 100),
                    100,
                    f"Analyzing {category_display}: {cur}/{tot}"
                ) if progress_callback else None
            )
            
            if status_callback:
                status_callback(f"💾 Phase 3/3: Saving {category_display} results...")
            
            # Save to database
            for group_files, similarity in duplicates:
                if self.is_stopped:
                    break
                
                dup_group = DuplicateGroup(
                    session_id=self.session_id,
                    file_type=category,
                    similarity_score=similarity
                )
                session.add(dup_group)
                session.flush()  # Get the group ID
                
                for file_info in group_files:
                    # Create thumbnail if applicable
                    thumbnail_path = None
                    if category in ['image', 'video']:
                        thumb_name = f"{dup_group.id}_{os.path.basename(file_info.path)}.jpg"
                        thumbnail_path = os.path.join(thumbnails_dir, thumb_name)
                        
                        if category == 'image':
                            detector.create_thumbnail(file_info.path, thumbnail_path)
                        elif category == 'video':
                            detector.create_thumbnail(file_info.path, thumbnail_path)
                    
                    file_entry = FileEntry(
                        group_id=dup_group.id,
                        file_path=file_info.path,
                        file_size=file_info.size,
                        modified_time=file_info.modified,
                        thumbnail_path=thumbnail_path
                    )
                    session.add(file_entry)
            
            session.commit()
        
        session.close()
        
        if status_callback and not self.is_stopped:
            status_callback("✅ Scan complete!")
    
    def _find_duplicates(self, files: List[FileInfo], detector, category: str,
                        progress_callback: Optional[Callable] = None) -> List[Tuple[List[FileInfo], float]]:
        """Find duplicate files using the given detector"""
        duplicates = []
        signatures = {}
        
        # Compute signatures
        total = len(files)
        for idx, file_info in enumerate(files):
            if self.is_stopped or self.is_paused:
                while self.is_paused and not self.is_stopped:
                    pass  # Wait while paused
                if self.is_stopped:
                    break
            
            if progress_callback:
                progress_callback(idx + 1, total)
            
            sig = detector.compute_signature(file_info.path)
            if sig:
                if sig not in signatures:
                    signatures[sig] = []
                signatures[sig].append(file_info)
        
        # For exact matches (archives, some documents)
        for sig, file_list in signatures.items():
            if len(file_list) > 1:
                duplicates.append((file_list, 1.0))
        
        # For fuzzy matches (images, documents, videos, code)
        if category in ['image', 'video', 'document', 'code']:
            self._find_similar_pairs(files, detector, duplicates, progress_callback)
        
        return duplicates
    
    def _find_similar_pairs(self, files: List[FileInfo], detector,
                           duplicates: List, progress_callback: Optional[Callable] = None):
        """Find similar (but not exact) duplicates"""
        processed_pairs = set()
        total_comparisons = (len(files) * (len(files) - 1)) // 2
        current = 0
        
        for i, file1 in enumerate(files):
            if self.is_stopped:
                break
            
            for j, file2 in enumerate(files[i+1:], start=i+1):
                if self.is_stopped:
                    break
                
                current += 1
                if progress_callback and current % 100 == 0:
                    progress_callback(current, total_comparisons)
                
                pair_key = tuple(sorted([file1.path, file2.path]))
                if pair_key in processed_pairs:
                    continue
                
                similarity = detector.compare_files(file1.path, file2.path)
                
                if similarity >= self.similarity_threshold:
                    processed_pairs.add(pair_key)
                    # Check if already in a group
                    found_group = False
                    for group, score in duplicates:
                        if file1 in group or file2 in group:
                            if file1 not in group:
                                group.append(file1)
                            if file2 not in group:
                                group.append(file2)
                            found_group = True
                            break
                    
                    if not found_group:
                        duplicates.append(([file1, file2], similarity))
    
    def pause(self):
        """Pause the scan"""
        self.is_paused = True
    
    def resume(self):
        """Resume the scan"""
        self.is_paused = False
    
    def stop(self):
        """Stop the scan"""
        self.is_stopped = True
        self.is_paused = False
