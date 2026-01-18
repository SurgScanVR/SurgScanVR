"""
nnUNet Prediction Engine
=========================
Manages the nnUNet model for medical image segmentation.
"""

import os
import gc
from typing import List, Tuple, Optional, Callable

import torch
import numpy as np
import nibabel as nib
from skimage import measure
import trimesh
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

from .config import ORGAN_LABELS


class InferenceEngine:
    """nnUNet prediction engine."""
    
    def __init__(self, model_folder: str):
        self.model_folder = model_folder
        self.predictor: Optional[nnUNetPredictor] = None
        self.device: Optional[torch.device] = None
    
    def initialize(self, log_callback: Callable = None) -> None:
        """Load and initialize the model."""
        def log(msg, tag="info"):
            if log_callback:
                log_callback(msg, tag)
        
        # Device detection
        if torch.cuda.is_available():
            self.device = torch.device('cuda')
            log("💻 GPU detected: Using CUDA", "success")
            torch.cuda.empty_cache()
            gc.collect()
        else:
            self.device = torch.device('cpu')
            log("💻 GPU not found, using CPU", "warning")
        
        # Create predictor
        self.predictor = nnUNetPredictor(
            tile_step_size=0.5,
            use_gaussian=True,
            use_mirroring=False,
            perform_everything_on_device=False,
            device=self.device,
            verbose=False,
            verbose_preprocessing=False,
            allow_tqdm=True
        )
        
        self.predictor.initialize_from_trained_model_folder(
            self.model_folder,
            use_folds=(0,),
            checkpoint_name='checkpoint_final.pth'
        )
        
        log("✓ Model loaded successfully", "success")
    
    def predict(self, input_path: str, output_path: str) -> str:
        """Perform segmentation prediction."""
        if self.predictor is None:
            raise RuntimeError("Engine not initialized!")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        self.predictor.predict_from_files(
            [[input_path]], [output_path],
            save_probabilities=False,
            overwrite=True,
            num_processes_preprocessing=2,
            num_processes_segmentation_export=2
        )
        
        # nnUNet may save as .nii.gz
        if os.path.exists(output_path + '.gz'):
            return output_path + '.gz'
        return output_path
    
    @property
    def is_loaded(self) -> bool:
        return self.predictor is not None


class MeshGenerator:
    """Generates OBJ meshes from NIfTI segmentation."""
    
    def __init__(self, smooth: bool = True, smooth_iterations: int = 2):
        self.smooth = smooth
        self.smooth_iterations = smooth_iterations
    
    def generate(
        self, 
        nifti_path: str, 
        output_dir: str,
        log_callback: Callable = None
    ) -> List[Tuple[int, str]]:
        """
        Generate OBJ meshes from NIfTI file.
        
        Returns:
            [(organ_label, obj_path), ...] list
        """
        def log(msg, tag="info"):
            if log_callback:
                log_callback(msg, tag)
        
        os.makedirs(output_dir, exist_ok=True)
        
        nii = nib.load(nifti_path)
        data = nii.get_fdata()
        spacing = nii.header.get_zooms()[:3]
        
        labels = np.unique(data)
        labels = labels[labels != 0]  # Skip background
        
        base_name = os.path.basename(nifti_path)
        base_name = base_name.replace('.nii.gz', '').replace('.nii', '')
        
        obj_files = []
        
        for label in labels:
            label_int = int(label)
            mask = (data == label).astype(np.uint8)
            
            try:
                verts, faces, normals, _ = measure.marching_cubes(
                    mask, level=0.5, spacing=spacing
                )
                
                mesh = trimesh.Trimesh(
                    vertices=verts, faces=faces, vertex_normals=normals
                )
                
                if self.smooth:
                    trimesh.smoothing.filter_laplacian(
                        mesh, iterations=self.smooth_iterations
                    )
                
                organ_name = ORGAN_LABELS.get(label_int, f"organ_{label_int}")
                out_path = os.path.join(output_dir, f"{base_name}_{organ_name}.obj")
                mesh.export(out_path, file_type='obj')
                
                obj_files.append((label_int, out_path))
                log(f"  {organ_name} mesh created", "info")
                
            except Exception as e:
                log(f"  Label {label_int} skipped: {e}", "warning")
        
        return obj_files
