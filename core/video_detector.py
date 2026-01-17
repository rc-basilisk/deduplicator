"""
Video duplicate detector using frame sampling and perceptual hashing.
"""
import os
from typing import Optional, List
import cv2
import imagehash
from PIL import Image
import numpy as np
from .base import BaseDetector


class VideoDetector(BaseDetector):
    """Detect duplicate videos using frame sampling"""
    
    def __init__(self, similarity_threshold: float = 0.95, sample_frames: int = 10):
        super().__init__(similarity_threshold)
        self.sample_frames = sample_frames
        self.cache = {}
    
    def extract_frames(self, file_path: str) -> List[np.ndarray]:
        """Extract sample frames from video"""
        try:
            cap = cv2.VideoCapture(file_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames == 0:
                return []
            
            # Calculate frame indices to sample
            if total_frames <= self.sample_frames:
                frame_indices = list(range(total_frames))
            else:
                frame_indices = [
                    int(i * total_frames / self.sample_frames) 
                    for i in range(self.sample_frames)
                ]
            
            frames = []
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
            
            cap.release()
            return frames
        except Exception as e:
            print(f"Error extracting frames from {file_path}: {e}")
            return []
    
    def compute_signature(self, file_path: str) -> Optional[str]:
        """Compute signature from video frames"""
        if file_path in self.cache:
            return self.cache[file_path]
        
        frames = self.extract_frames(file_path)
        if not frames:
            return None
        
        # Compute hash for each frame and concatenate
        hashes = []
        for frame in frames:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            frame_hash = imagehash.average_hash(pil_img, hash_size=8)
            hashes.append(str(frame_hash))
        
        signature = '|'.join(hashes)
        self.cache[file_path] = signature
        return signature
    
    def compare_files(self, file1: str, file2: str) -> float:
        """Compare two videos based on frame hashes"""
        sig1 = self.compute_signature(file1)
        sig2 = self.compute_signature(file2)
        
        if not sig1 or not sig2:
            return 0.0
        
        hashes1 = sig1.split('|')
        hashes2 = sig2.split('|')
        
        # Videos must have same number of sampled frames
        if len(hashes1) != len(hashes2):
            return 0.0
        
        # Calculate average similarity across all frame pairs
        similarities = []
        for h1, h2 in zip(hashes1, hashes2):
            hash1_obj = imagehash.hex_to_hash(h1)
            hash2_obj = imagehash.hex_to_hash(h2)
            distance = hash1_obj - hash2_obj
            similarity = 1.0 - (distance / 64.0)  # hash_size=8 -> max_distance=64
            similarities.append(similarity)
        
        return sum(similarities) / len(similarities)
    
    def create_thumbnail(self, file_path: str, output_path: str, size: tuple = (200, 200)):
        """Create a thumbnail from video's first frame"""
        try:
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            pil_img.thumbnail(size, Image.Resampling.LANCZOS)
            pil_img.save(output_path, 'JPEG', quality=85)
            return True
        except Exception as e:
            print(f"Error creating thumbnail for {file_path}: {e}")
            return False
