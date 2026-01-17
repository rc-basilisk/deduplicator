"""
Image duplicate detector using perceptual hashing.

Uses a combination of three hash types for robust duplicate detection:
- Average hash (ahash): Overall brightness pattern
- Perceptual hash (phash): DCT-based, captures visual structure
- Difference hash (dhash): Gradient-based, captures edges

Images are only considered duplicates if ALL three hashes are similar,
which dramatically reduces false positives.
"""
import os
from typing import Optional, Tuple
import imagehash
from PIL import Image
from .base import BaseDetector


class ImageDetector(BaseDetector):
    """Detect duplicate images using multi-hash perceptual hashing"""

    def __init__(self, similarity_threshold: float = 0.95, hash_size: int = 12):
        super().__init__(similarity_threshold)
        self.hash_size = hash_size  # Increased from 8 for better discrimination
        self.cache = {}  # Cache computed hashes

    def compute_signature(self, file_path: str) -> Optional[str]:
        """Compute multi-hash signature for image.

        Returns a combined signature of ahash|phash|dhash for robust matching.
        """
        if file_path in self.cache:
            return self.cache[file_path]

        try:
            if not os.path.exists(file_path):
                return None

            with Image.open(file_path) as img:
                img.verify()

            with Image.open(file_path) as img:
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')

                # Compute three different hash types for robustness
                ahash = imagehash.average_hash(img, hash_size=self.hash_size)
                phash = imagehash.phash(img, hash_size=self.hash_size)
                dhash = imagehash.dhash(img, hash_size=self.hash_size)

                # Combine into single signature with delimiter
                combined = f"{ahash}|{phash}|{dhash}"
                self.cache[file_path] = combined
                return combined

        except (IOError, OSError, Image.UnidentifiedImageError):
            return None
        except Exception as e:
            print(f"Warning: Could not process image {file_path}: {e}")
            return None

    def _parse_signature(self, sig: str) -> Optional[Tuple[str, str, str]]:
        """Parse combined signature into individual hashes."""
        parts = sig.split('|')
        if len(parts) != 3:
            return None
        return tuple(parts)

    def compare_files(self, file1: str, file2: str) -> float:
        """Compare two images and return similarity score"""
        hash1 = self.compute_signature(file1)
        hash2 = self.compute_signature(file2)

        if hash1 is None or hash2 is None:
            return 0.0

        return self.compare_signatures(hash1, hash2)

    def compare_signatures(self, sig1: str, sig2: str) -> float:
        """Compare two multi-hash signatures.

        Returns the MINIMUM similarity across all three hash types.
        This ensures that images must be similar in structure, gradients,
        AND overall appearance to be considered duplicates.
        """
        try:
            parts1 = self._parse_signature(sig1)
            parts2 = self._parse_signature(sig2)

            if not parts1 or not parts2:
                return 0.0

            max_distance = self.hash_size * self.hash_size
            similarities = []

            for h1_str, h2_str in zip(parts1, parts2):
                h1 = imagehash.hex_to_hash(h1_str)
                h2 = imagehash.hex_to_hash(h2_str)
                distance = h1 - h2
                sim = 1.0 - (distance / max_distance)
                similarities.append(sim)

            # Return MINIMUM similarity - all hashes must agree
            # This prevents false positives where only one hash type matches
            return min(similarities)

        except Exception:
            return 0.0
    
    def create_thumbnail(self, file_path: str, output_path: str, size: tuple = (200, 200)):
        """Create a thumbnail for an image"""
        try:
            with Image.open(file_path) as img:
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
                            img_rgba = img.convert('RGBA')
                            rgb_img.paste(img_rgba, mask=img_rgba.split()[-1])
                        else:
                            rgb_img = img.convert('RGB')
                    final_img = rgb_img
                elif img.mode not in ('RGB', 'L'):
                    final_img = img.convert('RGB')
                else:
                    final_img = img.copy()

                final_img.thumbnail(size, Image.Resampling.LANCZOS)
                final_img.save(output_path, 'JPEG', quality=85)
                return True
        except Exception:
            # Silently fail on thumbnail creation - not critical
            return False
