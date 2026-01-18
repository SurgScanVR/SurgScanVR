"""
Main Application
=================
Main application class that integrates all components.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime
from typing import Optional, Dict, List, Tuple

from .config import (
    COLORS, ORGAN_LABELS, 
    DEFAULT_OUTPUT_DIR, DEFAULT_UNITY_HOST, DEFAULT_UNITY_PORT,
    setup_nnunet_env
)
from .cache import PredictionCache
from .volume import VolumeCalculator
from .patient import PatientRecordManager
from .network import UnityClient
from .engine import InferenceEngine, MeshGenerator


class InferenceApp:
    """Main application class."""
    
    def __init__(self):
        self._init_window()
        self._init_variables()
        self._init_components()
        self._setup_ui()
        setup_nnunet_env(os.path.dirname(os.path.abspath(__file__)))
    
    # ==================== INITIALIZATION ====================
    
    def _init_window(self):
        """Initialize the window."""
        self.root = tk.Tk()
        self.root.title("Medical Image Segmentation - Patient Record System")
        self.root.geometry("1400x700")
        self.root.configure(bg=COLORS["bg"])
    
    def _init_variables(self):
        """Initialize Tkinter variables."""
        self.model_folder = tk.StringVar()
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        self.unity_host = tk.StringVar(value=DEFAULT_UNITY_HOST)
        self.unity_port = tk.StringVar(value=str(DEFAULT_UNITY_PORT))
        self.use_cache = tk.BooleanVar(value=True)
        
        # Patient information
        self.patient_name = tk.StringVar()
        self.patient_age = tk.StringVar()
        self.patient_gender = tk.StringVar(value="Male")
        self.chronic_disease = tk.StringVar()
        self.doctor_note: Optional[tk.Text] = None
        
        # State
        self.is_processing = False
        self.current_volume_data: Optional[Dict] = None
        self.current_obj_files: Optional[List[Tuple[int, str]]] = None
    
    def _init_components(self):
        """Initialize business logic components."""
        self.cache: Optional[PredictionCache] = None
        self.engine: Optional[InferenceEngine] = None
        self.mesh_generator = MeshGenerator()
        self.record_manager = PatientRecordManager()
    
    # ==================== USER INTERFACE ====================
    
    def _setup_ui(self):
        """Create UI components."""
        self._setup_styles()
        self._setup_layout()
    
    def _setup_styles(self):
        """Set up Tkinter styles."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["fg"], font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("TCheckbutton", background=COLORS["bg"], foreground=COLORS["fg"])
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabelframe", background=COLORS["bg"], foreground=COLORS["fg"])
        style.configure("TLabelframe.Label", background=COLORS["bg"], foreground=COLORS["accent"], font=("Segoe UI", 10, "bold"))
    
    def _setup_layout(self):
        """Create main layout."""
        # Container
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(main, text="🏥 Medical Image Segmentation", 
                        font=("Segoe UI", 18, "bold"), bg=COLORS["bg"], fg=COLORS["accent"])
        title.pack(pady=(0, 10))
        
        # Two-column layout
        content = ttk.Frame(main)
        content.pack(fill=tk.BOTH, expand=True)
        
        self._setup_left_panel(content)
        self._setup_right_panel(content)
    
    def _setup_left_panel(self, parent):
        """Left panel (controls)."""
        left = ttk.Frame(parent)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Scroll frame
        canvas = tk.Canvas(left, bg=COLORS["bg"], highlightthickness=0, width=500)
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Sections
        self._setup_file_section(scrollable)
        self._setup_patient_section(scrollable)
        self._setup_results_section(scrollable)
        self._setup_unity_section(scrollable)
        self._setup_buttons(scrollable)
        self._setup_progress(scrollable)
    
    def _setup_file_section(self, parent):
        """File selection section."""
        frame = ttk.LabelFrame(parent, text="📁 File Selection", padding=10)
        frame.pack(fill=tk.X, pady=5, padx=5)
        
        self._file_row(frame, "Model:", self.model_folder, self._browse_model)
        self._file_row(frame, "Image:", self.input_file, self._browse_image)
        self._file_row(frame, "Output:", self.output_dir, self._browse_output)
    
    def _file_row(self, parent, label, var, command):
        """File selection row."""
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text=label, width=10).pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=var, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(row, text="Browse", command=command, width=8).pack(side=tk.LEFT)
    
    def _setup_patient_section(self, parent):
        """Patient information section."""
        frame = ttk.LabelFrame(parent, text="👤 Patient Information", padding=10)
        frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Name, Age
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X, pady=3)
        ttk.Label(row1, text="Patient Name:", width=12).pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.patient_name, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(row1, text="Age:").pack(side=tk.LEFT, padx=(10, 5))
        ttk.Entry(row1, textvariable=self.patient_age, width=6).pack(side=tk.LEFT)
        
        # Gender
        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text="Gender:", width=12).pack(side=tk.LEFT)
        ttk.Radiobutton(row2, text="Male", variable=self.patient_gender, value="Male").pack(side=tk.LEFT)
        ttk.Radiobutton(row2, text="Female", variable=self.patient_gender, value="Female").pack(side=tk.LEFT, padx=10)
        
        # Chronic disease
        row3 = ttk.Frame(frame)
        row3.pack(fill=tk.X, pady=3)
        ttk.Label(row3, text="Chronic Disease:", width=12).pack(side=tk.LEFT)
        ttk.Entry(row3, textvariable=self.chronic_disease, width=30).pack(side=tk.LEFT, padx=5)
        
        # Doctor note
        row4 = ttk.Frame(frame)
        row4.pack(fill=tk.X, pady=3)
        ttk.Label(row4, text="Doctor Note:", width=12).pack(side=tk.LEFT, anchor=tk.N)
        self.doctor_note = tk.Text(row4, height=2, width=35, bg=COLORS["input_bg"], fg=COLORS["input_fg"], font=("Segoe UI", 9))
        self.doctor_note.pack(side=tk.LEFT, padx=5)
    
    def _setup_results_section(self, parent):
        """Analysis results section."""
        frame = ttk.LabelFrame(parent, text="📊 Analysis Results", padding=10)
        frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.results_text = tk.Text(frame, height=5, bg=COLORS["input_bg"], fg=COLORS["input_fg"],
                                   font=("Consolas", 9), state=tk.DISABLED)
        self.results_text.pack(fill=tk.X)
    
    def _setup_unity_section(self, parent):
        """Unity settings section."""
        frame = ttk.LabelFrame(parent, text="🎮 Unity Settings", padding=10)
        frame.pack(fill=tk.X, pady=5, padx=5)
        
        row = ttk.Frame(frame)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Host:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(row, textvariable=self.unity_host, width=12).pack(side=tk.LEFT)
        ttk.Label(row, text="Port:").pack(side=tk.LEFT, padx=(10, 5))
        ttk.Entry(row, textvariable=self.unity_port, width=6).pack(side=tk.LEFT)
        
        ttk.Checkbutton(frame, text="Use Cache", variable=self.use_cache).pack(anchor=tk.W, pady=5)
    
    def _setup_buttons(self, parent):
        """Buttons."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=10, padx=5)
        
        self.start_btn = tk.Button(frame, text="▶ PREDICT", font=("Segoe UI", 11, "bold"),
                                   bg=COLORS["success"], fg="white", padx=15, pady=6,
                                   command=self._on_predict)
        self.start_btn.pack(side=tk.LEFT, padx=3)
        
        tk.Button(frame, text="💾 SAVE", font=("Segoe UI", 10, "bold"),
                 bg="#2196f3", fg="white", padx=10, pady=6,
                 command=self._on_save).pack(side=tk.LEFT, padx=3)
        
        tk.Button(frame, text="🥽 SEND TO VR", font=("Segoe UI", 10, "bold"),
                 bg="#9c27b0", fg="white", padx=10, pady=6,
                 command=self._on_send_vr).pack(side=tk.LEFT, padx=3)
        
        tk.Button(frame, text="⏹", font=("Segoe UI", 10),
                 bg=COLORS["error"], fg="white", padx=8, pady=4,
                 command=self._on_stop).pack(side=tk.LEFT, padx=3)
    
    def _setup_progress(self, parent):
        """Progress bar and status."""
        self.progress = ttk.Progressbar(parent, mode='indeterminate', length=400)
        self.progress.pack(pady=5, padx=5)
        
        self.status_label = tk.Label(parent, text="Ready", font=("Segoe UI", 10),
                                    bg=COLORS["bg"], fg="#aaa")
        self.status_label.pack(pady=3)
    
    def _setup_right_panel(self, parent):
        """Right panel (console)."""
        frame = ttk.LabelFrame(parent, text="💻 Console - Process Status", padding=10)
        frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Big status
        self.big_status = tk.Label(frame, text="⭕ Ready - Waiting for process", 
                                   font=("Segoe UI", 13, "bold"), bg=COLORS["input_bg"], fg=COLORS["accent"],
                                   anchor="w", padx=10, pady=8)
        self.big_status.pack(fill=tk.X, pady=(0, 10))
        
        # Log text
        self.log_text = tk.Text(frame, width=50, bg=COLORS["console_bg"], fg=COLORS["console_fg"],
                               font=("Consolas", 10), wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Color tags
        self.log_text.tag_configure("info", foreground=COLORS["accent"])
        self.log_text.tag_configure("success", foreground=COLORS["success"])
        self.log_text.tag_configure("warning", foreground=COLORS["warning"])
        self.log_text.tag_configure("error", foreground=COLORS["error"])
        self.log_text.tag_configure("header", foreground=COLORS["header"], font=("Consolas", 10, "bold"))
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # ==================== FILE SELECTION ====================
    
    def _browse_model(self):
        path = filedialog.askdirectory(title="Select Model Folder")
        if path:
            self.model_folder.set(path)
    
    def _browse_image(self):
        path = filedialog.askopenfilename(
            title="Select NIfTI Image",
            filetypes=[("NIfTI", "*.nii *.nii.gz"), ("All", "*.*")]
        )
        if path:
            self.input_file.set(path)
    
    def _browse_output(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_dir.set(path)
    
    # ==================== HELPERS ====================
    
    def _log(self, message: str, tag: str = "info"):
        """Write message to console."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] ", "info")
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def _set_status(self, text: str, color: str = "#aaa"):
        self.status_label.configure(text=text, fg=color)
    
    def _set_big_status(self, text: str, color: str = None):
        color = color or COLORS["accent"]
        self.big_status.configure(text=text, fg=color)
        self.root.update_idletasks()
    
    def _update_results(self, data: Dict):
        """Display analysis results."""
        self.results_text.configure(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        text = f"🔹 Liver Volume: {data['liver_volume_ml']} ml\n"
        text += f"🔹 Tumor Count: {data['tumor_count']}\n"
        text += f"🔹 Total Tumor Volume: {data['total_tumor_volume_ml']} ml\n"
        
        if data['tumors']:
            text += "\n📍 Tumor Details:\n"
            for tumor in data['tumors']:
                text += f"   • Tumor {tumor['id']}: {tumor['volume_ml']} ml\n"
        
        self.results_text.insert(tk.END, text)
        self.results_text.configure(state=tk.DISABLED)
    
    def _get_patient_info(self) -> Dict:
        """Get patient information."""
        return {
            "name": self.patient_name.get(),
            "age": self.patient_age.get(),
            "gender": self.patient_gender.get(),
            "chronic_disease": self.chronic_disease.get(),
            "doctor_note": self.doctor_note.get("1.0", tk.END).strip() if self.doctor_note else ""
        }
    
    # ==================== EVENT HANDLERS ====================
    
    def _on_predict(self):
        """Predict button clicked."""
        if self.is_processing:
            return
        
        if not self.model_folder.get():
            messagebox.showerror("Error", "Select a model folder!")
            return
        if not self.input_file.get():
            messagebox.showerror("Error", "Select an image file!")
            return
        
        self.is_processing = True
        self.progress.start(10)
        self.start_btn.configure(state=tk.DISABLED)
        
        thread = threading.Thread(target=self._run_prediction, daemon=True)
        thread.start()
    
    def _on_save(self):
        """Save button clicked."""
        if not self.input_file.get():
            messagebox.showerror("Error", "Select an image first!")
            return
        if not self.current_volume_data:
            messagebox.showerror("Error", "Run prediction first!")
            return
        
        try:
            path = self.record_manager.save(
                self.input_file.get(),
                self._get_patient_info(),
                self.current_volume_data
            )
            self._log(f"✓ Patient record saved: {os.path.basename(path)}", "success")
            messagebox.showinfo("Success", f"Patient record saved:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Save error: {e}")
    
    def _on_send_vr(self):
        """Send to VR button clicked."""
        if not self.current_obj_files:
            messagebox.showerror("Error", "Run prediction first!")
            return
        if not self.current_volume_data:
            messagebox.showerror("Error", "Analysis data not found!")
            return
        
        thread = threading.Thread(target=self._send_to_unity, daemon=True)
        thread.start()
    
    def _on_stop(self):
        """Stop button clicked."""
        self.is_processing = False
        self._finish()
    
    def _finish(self):
        """Finish the process."""
        self.is_processing = False
        self.progress.stop()
        self.start_btn.configure(state=tk.NORMAL)
    
    # ==================== BUSINESS LOGIC ====================
    
    def _run_prediction(self):
        """Prediction process."""
        try:
            # Check cache
            if self.use_cache.get():
                if self.cache is None:
                    self.cache = PredictionCache()
                
                if self.cache.is_cached(self.input_file.get()):
                    self._handle_cached_result()
                    return
            
            # New prediction
            self._run_full_prediction()
            
        except Exception as e:
            self._set_big_status("❌ ERROR OCCURRED", COLORS["error"])
            self._log(f"❌ ERROR: {e}", "error")
        
        self._finish()
    
    def _handle_cached_result(self):
        """Load result from cache."""
        cached = self.cache.get(self.input_file.get())
        
        self._set_big_status("⚡ Loading from Cache...", COLORS["accent"])
        self._log("═" * 50, "header")
        self._log("⚡ This image was processed before - Loading from cache", "success")
        
        if cached.get("prediction_path") and os.path.exists(cached["prediction_path"]):
            self.current_volume_data = VolumeCalculator.calculate(cached["prediction_path"])
            self.root.after(0, lambda: self._update_results(self.current_volume_data))
        
        self.current_obj_files = cached["obj_files"]
        self._log(f"✓ {len(cached['obj_files'])} mesh files ready", "success")
        self._set_big_status("✅ Ready - Can be sent to VR", COLORS["success"])
        self._finish()
    
    def _run_full_prediction(self):
        """Full prediction process."""
        # Header
        self._log("═" * 50, "header")
        self._log("🚀 PREDICTION PROCESS STARTING", "header")
        self._log("═" * 50, "header")
        
        # Load model
        self._set_big_status("🔄 Loading Model...", COLORS["warning"])
        self._log("⏳ Loading AI model...", "warning")
        
        if self.engine is None or not self.engine.is_loaded:
            self.engine = InferenceEngine(self.model_folder.get())
            self.engine.initialize(self._log)
        else:
            self._log("✓ Model already loaded", "success")
        
        # Prediction
        self._set_big_status("🧠 Making Prediction... (May take a few minutes)", COLORS["warning"])
        self._log("", "info")
        self._log("🧠 PERFORMING SEGMENTATION PREDICTION...", "warning")
        self._log(f"   Image: {os.path.basename(self.input_file.get())}", "info")
        
        output_name = os.path.basename(self.input_file.get())
        output_name = output_name.replace('.nii.gz', '_pred.nii').replace('.nii', '_pred.nii')
        output_path = os.path.join(self.output_dir.get(), output_name)
        
        pred_path = self.engine.predict(self.input_file.get(), output_path)
        self._log("✓ Segmentation prediction completed!", "success")
        
        # Volume
        self._log("", "info")
        self._log("📊 PERFORMING VOLUME ANALYSIS...", "warning")
        self.current_volume_data = VolumeCalculator.calculate(pred_path)
        self.root.after(0, lambda: self._update_results(self.current_volume_data))
        
        self._log(f"   🔹 Liver Volume: {self.current_volume_data['liver_volume_ml']} ml", "success")
        self._log(f"   🔹 Tumor Count: {self.current_volume_data['tumor_count']}", "success")
        self._log("✓ Volume analysis completed", "success")
        
        # Mesh
        self._set_big_status("🚧 Creating 3D Meshes...", COLORS["warning"])
        self._log("", "info")
        self._log("🚧 CREATING 3D MESH FILES...", "warning")
        
        unity_dir = os.path.join(self.output_dir.get(), "unity_assets")
        self.current_obj_files = self.mesh_generator.generate(pred_path, unity_dir, self._log)
        self._log(f"✓ {len(self.current_obj_files)} 3D meshes created", "success")
        
        # Save to cache
        if self.use_cache.get() and self.cache:
            self.cache.save(self.input_file.get(), {
                "prediction_path": pred_path,
                "obj_files": self.current_obj_files
            })
            self._log("✓ Results saved to cache", "success")
        
        # Completed
        self._log("", "info")
        self._log("═" * 50, "header")
        self._log("✅ ALL PROCESSES COMPLETED SUCCESSFULLY!", "success")
        self._log("═" * 50, "header")
        self._log("👉 Click 'Send to VR' button", "info")
        
        self._set_big_status("✅ Completed - Can be sent to VR", COLORS["success"])
    
    def _send_to_unity(self):
        """Send to Unity."""
        self._set_big_status("🥽 Sending to VR Headset...", "#9c27b0")
        self._log("", "info")
        self._log("═" * 50, "header")
        self._log("🥽 SENDING TO VR HEADSET", "header")
        self._log("═" * 50, "header")
        self._log(f"   Target: {self.unity_host.get()}:{self.unity_port.get()}", "info")
        self._log("   Establishing connection...", "warning")
        
        client = UnityClient(
            host=self.unity_host.get(),
            port=int(self.unity_port.get())
        )
        
        patient_data = {
            "patient": self._get_patient_info(),
            "analysis": self.current_volume_data
        }
        
        success = client.send(self.current_obj_files, patient_data, self._log)
        
        if success:
            self._log("", "info")
            self._log("═" * 50, "header")
            self._log("✅ SUCCESSFULLY SENT TO VR HEADSET!", "success")
            self._log("═" * 50, "header")
            self._set_big_status("✅ Sent to VR Headset!", COLORS["success"])
        else:
            self._set_big_status("❌ VR Connection Error", COLORS["error"])
    
    # ==================== RUN ====================
    
    def run(self):
        """Start the application."""
        self.root.mainloop()
