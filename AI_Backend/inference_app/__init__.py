"""
Inference GUI - Main Module
============================
This package provides a user interface for medical image segmentation.

Modules:
    - config: Constants and configuration
    - cache: Cache management
    - volume: Volume calculation
    - patient: Patient record management
    - network: Unity TCP communication
    - engine: nnUNet prediction engine
    - ui: Tkinter UI components
    - app: Main application class

Usage:
    python -m inference_app
    or
    python run.py
"""

from .app import InferenceApp

__all__ = ['InferenceApp']
__version__ = '1.0.0'
