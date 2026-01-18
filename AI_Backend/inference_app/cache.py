"""
Cache Management
=================
Caches and manages prediction results.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional, Any

from .config import DEFAULT_CACHE_DIR


class PredictionCache:
    """File-based prediction cache."""
    
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "cache_index.json")
        self.cache_data: Dict[str, Dict] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Create cache directory and load existing data."""
        os.makedirs(self.cache_dir, exist_ok=True)
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.cache_data = json.load(f)
    
    def _get_hash(self, file_path: str) -> str:
        """Calculate the MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def is_cached(self, image_path: str) -> bool:
        """Check if the image is cached."""
        key = self._get_hash(image_path)
        if key not in self.cache_data:
            return False
        # Check if OBJ files exist
        for _, obj_path in self.cache_data[key].get("obj_files", []):
            if not os.path.exists(obj_path):
                return False
        return True
    
    def get(self, image_path: str) -> Optional[Dict]:
        """Get result from cache."""
        return self.cache_data.get(self._get_hash(image_path))
    
    def save(self, image_path: str, result: Dict) -> None:
        """Save result to cache."""
        key = self._get_hash(image_path)
        result["timestamp"] = datetime.now().isoformat()
        self.cache_data[key] = result
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache_data = {}
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)
