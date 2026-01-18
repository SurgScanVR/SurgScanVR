"""
Configuration and Constants
============================
Constant values used throughout the application.
"""

import os

# Organ labels (according to dataset.json)
ORGAN_LABELS = {
    0: "background",
    1: "spleen",
    2: "kidneys",
    3: "pancreas",
    4: "stomach",
    5: "heart",
    6: "duodenum",
    7: "tumsomething",
    8: "liver",
    9: "tumor"
}

# Important labels for volume calculation
LIVER_LABEL = 8
TUMOR_LABEL = 9

# Default directories
DEFAULT_OUTPUT_DIR = "predictions"
DEFAULT_CACHE_DIR = "prediction_cache"
DEFAULT_RECORDS_DIR = "patient_records"
DEFAULT_UNITY_ASSETS_DIR = "unity_assets"

# Unity connection settings
DEFAULT_UNITY_HOST = "127.0.0.1"
DEFAULT_UNITY_PORT = 5555

# UI colors
COLORS = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "accent": "#4fc3f7",
    "success": "#4caf50",
    "warning": "#ffa726",
    "error": "#f44336",
    "header": "#e91e63",
    "console_bg": "#1a1a1a",
    "console_fg": "#00ff00",
    "input_bg": "#252526",
    "input_fg": "#d4d4d4"
}

# PyTorch memory configuration
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"


def setup_nnunet_env(base_dir: str) -> None:
    """Set up nnUNet environment variables."""
    for name in ['nnUNet_raw', 'nnUNet_preprocessed', 'nnUNet_results']:
        path = os.path.join(base_dir, f"{name}_dummy")
        os.makedirs(path, exist_ok=True)
        os.environ[name] = path
