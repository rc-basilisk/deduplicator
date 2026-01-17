"""
Auto-sorting utility for organizing files into categories.
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Callable
from core.base import FileScanner


class AutoSorter:
    """Automatically sort files into categorized folders"""
    
    CATEGORY_MAPPING = {
        'images': FileScanner.SUPPORTED_EXTENSIONS['image'],
        'documents': FileScanner.SUPPORTED_EXTENSIONS['document'],
        'videos': FileScanner.SUPPORTED_EXTENSIONS['video'],
        'archives': FileScanner.SUPPORTED_EXTENSIONS['archive'],
        'code': FileScanner.SUPPORTED_EXTENSIONS['code'],
        'others': set()  # Catch-all
    }
    
    def __init__(self, source_paths: List[str], destination: str):
        self.source_paths = source_paths
        self.destination = os.path.expanduser(destination)
        self.stats = {
            'total': 0,
            'moved': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def sort_files(self, progress_callback: Optional[Callable] = None,
                   status_callback: Optional[Callable] = None):
        """
        Sort files from source paths into categorized destination folders
        
        Args:
            progress_callback: Callback(current, total, filepath)
            status_callback: Callback(status_message)
        """
        # Create destination category folders
        os.makedirs(self.destination, exist_ok=True)
        category_dirs = {}
        for category in self.CATEGORY_MAPPING.keys():
            cat_dir = os.path.join(self.destination, category)
            os.makedirs(cat_dir, exist_ok=True)
            category_dirs[category] = cat_dir
        
        # Collect all files
        all_files = []
        for source_path in self.source_paths:
            if os.path.isfile(source_path):
                all_files.append(source_path)
            elif os.path.isdir(source_path):
                for root, dirs, files in os.walk(source_path):
                    for filename in files:
                        all_files.append(os.path.join(root, filename))
        
        self.stats['total'] = len(all_files)
        
        if status_callback:
            status_callback(f"Found {self.stats['total']} files to sort")
        
        # Sort each file
        for idx, file_path in enumerate(all_files):
            if progress_callback:
                progress_callback(idx + 1, self.stats['total'], file_path)
            
            category = self._get_file_category(file_path)
            dest_dir = category_dirs[category]
            
            try:
                # Handle filename conflicts
                dest_path = self._get_unique_path(dest_dir, os.path.basename(file_path))
                shutil.move(file_path, dest_path)
                self.stats['moved'] += 1
            except Exception as e:
                print(f"Error moving {file_path}: {e}")
                self.stats['failed'] += 1
        
        if status_callback:
            status_callback(f"Sorting complete! Moved: {self.stats['moved']}, "
                          f"Failed: {self.stats['failed']}")
        
        return self.stats
    
    def _get_file_category(self, file_path: str) -> str:
        """Determine which category a file belongs to"""
        ext = os.path.splitext(file_path)[1].lower()
        
        for category, extensions in self.CATEGORY_MAPPING.items():
            if category == 'others':
                continue
            if ext in extensions:
                return category
        
        return 'others'
    
    def _get_unique_path(self, directory: str, filename: str) -> str:
        """Get a unique file path, adding numbers if file exists"""
        base_path = os.path.join(directory, filename)
        
        if not os.path.exists(base_path):
            return base_path
        
        name, ext = os.path.splitext(filename)
        counter = 1
        
        while True:
            new_name = f"{name}_{counter}{ext}"
            new_path = os.path.join(directory, new_name)
            if not os.path.exists(new_path):
                return new_path
            counter += 1


class MLImageCategorizer:
    """ML-based image categorization using Ollama"""
    
    CATEGORIES = [
        'screenshots',
        'photos', 
        'memes',
        'artworks',
        'anime_manga',
        'schematics_infographics',
        'others'
    ]
    
    def __init__(self, ollama_model: str = 'llava'):
        self.model = ollama_model
        self.cache_dir = os.path.expanduser('~/.cache/deduplicator/ml_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def categorize_image(self, image_path: str) -> str:
        """Categorize a single image using Ollama vision model"""
        try:
            import requests
            import base64
            
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Prepare prompt
            prompt = (
                "Categorize this image into ONE of these categories: "
                "screenshots, photos, memes, artworks, anime_manga, "
                "schematics_infographics, others. "
                "Respond with ONLY the category name, nothing else."
            )
            
            # Call Ollama API
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'images': [image_data],
                    'stream': False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                category = result.get('response', '').strip().lower()
                
                # Validate category
                if category in self.CATEGORIES:
                    return category
            
            return 'others'
        except Exception as e:
            print(f"Error categorizing {image_path}: {e}")
            return 'others'
    
    def categorize_folder(self, folder_path: str, 
                         progress_callback: Optional[Callable] = None):
        """Categorize all images in a folder"""
        image_extensions = FileScanner.SUPPORTED_EXTENSIONS['image']
        
        # Find all images
        images = []
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                if os.path.splitext(filename)[1].lower() in image_extensions:
                    images.append(os.path.join(root, filename))
        
        total = len(images)
        categorized = {}
        
        for idx, image_path in enumerate(images):
            if progress_callback:
                progress_callback(idx + 1, total, image_path)
            
            category = self.categorize_image(image_path)
            
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(image_path)
        
        return categorized
    
    def sort_by_category(self, categorized: Dict[str, List[str]], 
                        destination: str):
        """Move categorized images to appropriate subfolders"""
        for category, image_paths in categorized.items():
            cat_dir = os.path.join(destination, category)
            os.makedirs(cat_dir, exist_ok=True)
            
            for image_path in image_paths:
                try:
                    filename = os.path.basename(image_path)
                    dest_path = os.path.join(cat_dir, filename)
                    
                    # Handle duplicates
                    if os.path.exists(dest_path):
                        name, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(dest_path):
                            dest_path = os.path.join(cat_dir, f"{name}_{counter}{ext}")
                            counter += 1
                    
                    shutil.move(image_path, dest_path)
                except Exception as e:
                    print(f"Error moving {image_path}: {e}")
