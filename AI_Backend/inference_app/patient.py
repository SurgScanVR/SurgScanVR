"""
Patient Record Management
==========================
Saves and loads patient information as JSON.
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional

from .config import DEFAULT_RECORDS_DIR


class PatientRecordManager:
    """Class that manages patient records."""
    
    def __init__(self, records_dir: str = DEFAULT_RECORDS_DIR):
        self.records_dir = records_dir
        os.makedirs(records_dir, exist_ok=True)
    
    def save(self, image_name: str, patient_info: Dict, volume_data: Dict) -> str:
        """
        Save patient record as JSON.
        
        Args:
            image_name: Image file name
            patient_info: Patient information dict
            volume_data: Volume analysis results
            
        Returns:
            Path to the saved JSON file
        """
        record = {
            "record_date": datetime.now().isoformat(),
            "image_file": image_name,
            "patient_info": patient_info,
            "analysis_results": volume_data
        }
        
        base_name = os.path.splitext(os.path.basename(image_name))[0]
        base_name = base_name.replace('.nii', '')
        json_path = os.path.join(self.records_dir, f"{base_name}_patient_record.json")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        
        return json_path
    
    def load(self, json_path: str) -> Optional[Dict]:
        """Load patient record."""
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
