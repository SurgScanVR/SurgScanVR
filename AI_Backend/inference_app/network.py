"""
Unity Network Communication
============================
Sends mesh and patient data to Unity via TCP.
"""

import socket
import struct
import json
import time
from typing import List, Tuple, Dict, Callable

from .config import DEFAULT_UNITY_HOST, DEFAULT_UNITY_PORT


class UnityClient:
    """Client that establishes TCP connection to Unity."""
    
    def __init__(
        self, 
        host: str = DEFAULT_UNITY_HOST, 
        port: int = DEFAULT_UNITY_PORT,
        timeout: int = 10
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
    
    def send(
        self, 
        obj_files: List[Tuple[int, str]], 
        patient_data: Dict,
        log_callback: Callable = None
    ) -> bool:
        """
        Send mesh and patient data to Unity.
        
        Args:
            obj_files: [(organ_label, obj_path), ...] list
            patient_data: Patient and analysis data
            log_callback: Callback function for log messages
            
        Returns:
            True: Success, False: Failure
        """
        def log(msg, tag="info"):
            if log_callback:
                log_callback(msg, tag)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            log("   ✓ Connection established!", "success")
            
            # Send JSON patient data
            log("   📋 Sending patient information...", "warning")
            json_bytes = json.dumps(patient_data, ensure_ascii=False).encode('utf-8')
            sock.sendall(struct.pack('!I', len(json_bytes)))
            sock.sendall(json_bytes)
            log("   ✓ Patient information sent", "success")
            
            # Mesh count
            log(f"   🎮 Sending {len(obj_files)} 3D meshes...", "warning")
            sock.sendall(struct.pack('!I', len(obj_files)))
            
            # Send each mesh
            for organ_label, obj_path in obj_files:
                sock.sendall(struct.pack('!I', organ_label))
                with open(obj_path, 'rb') as f:
                    data = f.read()
                sock.sendall(struct.pack('!I', len(data)))
                sock.sendall(data)
                time.sleep(0.1)
            
            sock.close()
            return True
            
        except ConnectionRefusedError:
            log("❌ VR headset connection refused!", "error")
            log("   Make sure Unity is running.", "warning")
            return False
        except Exception as e:
            log(f"❌ VR headset connection error: {e}", "error")
            return False
