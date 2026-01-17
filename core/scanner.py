"""
Main scanning engine that coordinates duplicate detection.
"""
import os
import time
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
                 file_types: List[str], similarity_threshold: float = 0.95,
                 thread_count: int = 4):
        self.db = db
        self.session_id = session_id
        self.file_types = file_types
        self.similarity_threshold = similarity_threshold
        self.thread_count = thread_count  # For future parallel processing
        
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

                # Only create one thumbnail per group (for the first file)
                # This optimization reduces disk I/O and processing time
                group_thumbnail_path = None
                if category in ['image', 'video'] and group_files:
                    first_file = group_files[0]
                    thumb_name = f"{dup_group.id}_representative.jpg"
                    group_thumbnail_path = os.path.join(thumbnails_dir, thumb_name)
                    detector.create_thumbnail(first_file.path, group_thumbnail_path)

                for file_info in group_files:
                    file_entry = FileEntry(
                        group_id=dup_group.id,
                        file_path=file_info.path,
                        file_size=file_info.size,
                        modified_time=file_info.modified,
                        thumbnail_path=group_thumbnail_path  # All files in group share the same thumbnail
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
        # Pre-compute all signatures into a dict (addresses Phase 3.8)
        file_signatures: Dict[str, str] = {}
        signature_groups: Dict[str, List[FileInfo]] = defaultdict(list)

        # Phase 1: Compute all signatures upfront
        total = len(files)
        for idx, file_info in enumerate(files):
            if self.is_stopped or self.is_paused:
                while self.is_paused and not self.is_stopped:
                    time.sleep(0.1)  # Sleep to avoid busy-wait CPU consumption
                if self.is_stopped:
                    break

            if progress_callback:
                progress_callback(idx + 1, total)

            sig = detector.compute_signature(file_info.path)
            if sig:
                file_signatures[file_info.path] = sig
                signature_groups[sig].append(file_info)

        # Phase 2: Find exact matches (same signature)
        for sig, file_list in signature_groups.items():
            if len(file_list) > 1:
                duplicates.append((file_list, 1.0))

        # Phase 3: For fuzzy matches, use prefix-based grouping to reduce O(n^2)
        if category in ['image', 'video', 'document', 'code']:
            self._find_similar_pairs_optimized(
                files, detector, file_signatures, duplicates, progress_callback
            )

        return duplicates

    def _find_similar_pairs_optimized(self, files: List[FileInfo], detector,
                                      file_signatures: Dict[str, str],
                                      duplicates: List,
                                      progress_callback: Optional[Callable] = None):
        """Find similar duplicates using prefix-based grouping to reduce comparisons"""
        # Group files by signature prefix (first 4 chars) for locality-sensitive hashing
        prefix_groups: Dict[str, List[FileInfo]] = defaultdict(list)
        prefix_len = 4  # First 4 characters of hash

        for file_info in files:
            sig = file_signatures.get(file_info.path)
            if sig:
                # Use first 4 chars as bucket key
                prefix = sig[:prefix_len] if len(sig) >= prefix_len else sig
                prefix_groups[prefix].append(file_info)

        # Track which files are already in a duplicate group
        file_to_group: Dict[str, int] = {}
        for idx, (group_files, _) in enumerate(duplicates):
            for f in group_files:
                file_to_group[f.path] = idx

        processed_pairs = set()
        total_comparisons = sum(
            (len(group) * (len(group) - 1)) // 2 for group in prefix_groups.values()
        )
        current = 0

        # Only compare files within the same prefix group
        for prefix, group_files in prefix_groups.items():
            if len(group_files) < 2:
                continue

            for i, file1 in enumerate(group_files):
                if self.is_stopped:
                    return

                sig1 = file_signatures.get(file1.path)
                if not sig1:
                    continue

                for file2 in group_files[i + 1:]:
                    if self.is_stopped:
                        return

                    current += 1
                    if progress_callback and current % 100 == 0:
                        progress_callback(current, max(total_comparisons, 1))

                    pair_key = tuple(sorted([file1.path, file2.path]))
                    if pair_key in processed_pairs:
                        continue

                    sig2 = file_signatures.get(file2.path)
                    if not sig2:
                        continue

                    # Skip if already exact match (same signature)
                    if sig1 == sig2:
                        continue

                    # Use pre-computed signatures for comparison
                    similarity = detector.compare_signatures(sig1, sig2)

                    if similarity >= self.similarity_threshold:
                        processed_pairs.add(pair_key)
                        # Check if already in a group
                        group1_idx = file_to_group.get(file1.path)
                        group2_idx = file_to_group.get(file2.path)

                        if group1_idx is not None and group2_idx is not None:
                            # Both already in groups - merge if different
                            if group1_idx != group2_idx:
                                # Keep first group, merge second into it
                                duplicates[group1_idx][0].extend(duplicates[group2_idx][0])
                                for f in duplicates[group2_idx][0]:
                                    file_to_group[f.path] = group1_idx
                                duplicates[group2_idx] = ([], 0)  # Mark as empty
                        elif group1_idx is not None:
                            # Add file2 to file1's group
                            duplicates[group1_idx][0].append(file2)
                            file_to_group[file2.path] = group1_idx
                        elif group2_idx is not None:
                            # Add file1 to file2's group
                            duplicates[group2_idx][0].append(file1)
                            file_to_group[file1.path] = group2_idx
                        else:
                            # Create new group
                            new_idx = len(duplicates)
                            duplicates.append(([file1, file2], similarity))
                            file_to_group[file1.path] = new_idx
                            file_to_group[file2.path] = new_idx

        # Remove empty groups from merging
        duplicates[:] = [(g, s) for g, s in duplicates if len(g) > 0]
    
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
