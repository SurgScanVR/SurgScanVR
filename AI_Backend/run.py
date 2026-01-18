#!/usr/bin/env python3
"""
Medical Image Segmentation - Launcher
======================================
Run the application with: python run.py
"""

from inference_app import InferenceApp

if __name__ == '__main__':
    app = InferenceApp()
    app.run()
