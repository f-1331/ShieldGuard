import sys
import os
import traceback
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        info = {
            "python_version": sys.version,
            "sys_path": sys.path,
            "cwd": os.getcwd(),
            "env_keys": list(os.environ.keys())
        }
        
        # Test importing backend.main
        for p in [str(os.getcwd()), "/var/task", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]:
            if p not in sys.path:
                sys.path.insert(0, p)
                
        try:
            from backend.main import app
            info["import_status"] = "success"
            info["routes"] = [getattr(r, "path", str(r)) for r in app.routes]
        except Exception as e:
            info["import_status"] = "failed"
            info["error"] = str(e)
            info["traceback"] = traceback.format_exc()
            
        self.wfile.write(json.dumps(info, indent=2).encode('utf-8'))
