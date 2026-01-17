"""
Image duplicate detector using perceptual hashing.
"""
import os
from typing import Optional
import imagehash
from PIL import Image
from .base import BaseDetector


class ImageDetector(BaseDetector):
    """Detect duplicate images using perceptual hashing"""
    
    def __init__(self, similarity_threshold: float = 0.95, hash_size: int = 8):
        super().__init__(similarity_threshold)
        self.hash_size = hash_size
        self.cache = {}  # Cache computed hashes
    
    def compute_signature(self, file_path: str) -> Optional[str]:
        """Compute perceptual hash for image"""
        if file_path in self.cache:
            return self.cache[file_path]
        
        try:
            # Check if file exists and is readable
            if not os.path.exists(file_path):
                return None
            
            # Try to open and verify it's a valid image
            img = Image.open(file_path)
            img.verify()  # Verify it's not corrupted
            
            # Reopen after verify (verify closes the file)
            img = Image.open(file_path)
            
            # Convert to RGB if needed
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Use average hash (fast and effective)
            img_hash = imagehash.average_hash(img, hash_size=self.hash_size)
            hash_str = str(img_hash)
            self.cache[file_path] = hash_str
            return hash_str
        except (IOError, OSError, Image.UnidentifiedImageError) as e:
            # Silently skip corrupted or invalid images
            return None
        except Exception as e:
            # Log unexpected errors but don't crash
            print(f"Warning: Could not process image {file_path}: {e}")
            return None
    
    def compare_files(self, file1: str, file2: str) -> float:
        """Compare two images and return similarity score"""
        hash1 = self.compute_signature(file1)
        hash2 = self.compute_signature(file2)
        
        if hash1 is None or hash2 is None:
            return 0.0
        
        # Convert back to ImageHash objects
        hash1_obj = imagehash.hex_to_hash(hash1)
        hash2_obj = imagehash.hex_to_hash(hash2)
        
        # Calculate Hamming distance
        distance = hash1_obj - hash2_obj
        
        # Convert to similarity score (0.0-1.0)
        # Max possible distance for hash_size=8 is 64
        max_distance = self.hash_size * self.hash_size
        similarity = 1.0 - (distance / max_distance)
        
        return similarity
    
    def create_thumbnail(self, file_path: str, output_path: str, size: tuple = (200, 200)):
        """Create a thumbnail for an image"""
        try:
            img = Image.open(file_path)
            
            # Convert RGBA/P to RGB for JPEG compatibility
            if img.mode in ('RGBA', 'P', 'LA'):
                # Create white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                # If image has transparency, paste it on white background
                if img.mode == 'RGBA' or img.mode == 'LA':
                    rgb_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                elif img.mode == 'P':
                    # Handle palette mode (like GIFs)
                    if 'transparency' in img.info:
                        img = img.convert('RGBA')
                        rgb_img.paste(img, mask=img.split()[-1])
                    else:
                        rgb_img = img.convert('RGB')
                img = rgb_img
            elif img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path, 'JPEG', quality=85)
            return True
        except Exception as e:
            # Silently fail on thumbnail creation - not critical
            return False
