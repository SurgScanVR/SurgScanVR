"""
Volume Calculation
==================
Calculates liver and tumor volumes.
"""

import numpy as np
import nibabel as nib
from typing import Dict, List
from scipy import ndimage

from .config import LIVER_LABEL, TUMOR_LABEL


class VolumeCalculator:
    """Class that calculates organ and tumor volumes."""
    
    @staticmethod
    def calculate(
        nifti_path: str, 
        liver_label: int = LIVER_LABEL, 
        tumor_label: int = TUMOR_LABEL
    ) -> Dict:
        """
        Calculate liver and tumor volumes.
        
        Args:
            nifti_path: NIfTI segmentation file
            liver_label: Liver label value
            tumor_label: Tumor label value
            
        Returns:
            dict: liver_volume_ml, tumor_count, tumors, total_tumor_volume_ml
        """
        nii = nib.load(nifti_path)
        data = nii.get_fdata()
        spacing = nii.header.get_zooms()[:3]  # in mm
        
        # Voxel volume (mm³ -> ml: 1 ml = 1000 mm³)
        voxel_volume_ml = (spacing[0] * spacing[1] * spacing[2]) / 1000.0
        
        result = {
            'liver_volume_ml': 0.0,
            'tumor_count': 0,
            'tumors': [],
            'total_tumor_volume_ml': 0.0
        }
        
        # Liver volume
        liver_voxels = np.sum(data == liver_label)
        result['liver_volume_ml'] = round(liver_voxels * voxel_volume_ml, 2)
        
        # Tumor analysis - connected components
        tumor_mask = (data == tumor_label).astype(np.uint8)
        
        if np.sum(tumor_mask) > 0:
            labeled_tumors, num_tumors = ndimage.label(tumor_mask)
            result['tumor_count'] = num_tumors
            
            for i in range(1, num_tumors + 1):
                tumor_voxels = np.sum(labeled_tumors == i)
                tumor_volume = round(tumor_voxels * voxel_volume_ml, 2)
                result['tumors'].append({'id': i, 'volume_ml': tumor_volume})
                result['total_tumor_volume_ml'] += tumor_volume
            
            result['total_tumor_volume_ml'] = round(result['total_tumor_volume_ml'], 2)
        
        return result
