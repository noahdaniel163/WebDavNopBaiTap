import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import threading
import sys
import os
import webbrowser
import logging
import requests
import multiprocessing
import queue
import socket
from waitress import serve
from app import app, reload_config, CONFIG_FILE

# Helper class to redirect stdout/stderr to a multiprocessing Queue
class QueueWriter:
    def __init__(self, q):
        self.queue = q

    def write(self, msg):
        if msg:
            self.queue.put(msg)

    def flush(self):
        pass

def run_waitress_server(host, port, log_queue):
    # Redirect stdout/stderr to queue in this child process
    sys.stdout = QueueWriter(log_queue)
    sys.stderr = QueueWriter(log_queue)
    
    # We need to ensure app loads correct config in this process
    # But since config.json is saved before this process starts, app.py will read it on import/run.
    # Re-importing app inside process or relying on process fork?
    # On Windows, multiprocessing spawns fresh, so app is imported fresh.
    # config.json acts as the source of truth.
    
    print(f"Initializing Waitress Server on {host}:{port}...")
    try:
        from app import app
        # Ensure 'app' uses the secret key from config if needed, though secure_filename/sessions might need it.
        # app module init code runs on import.
        
        serve(app, host=host, port=port, threads=16)
    except Exception as e:
        print(f"Server Error: {e}")

class RedirectText:
    def __init__(self, text_ctrl, root):
        self.output = text_ctrl
        self.root = root

    def write(self, string):
        # Schedule the update on the main thread to avoid GUI freezing/crashing
        self.root.after(0, self._safe_write, string)

    def _safe_write(self, string):
        try:
            self.output.insert(tk.END, string)
            self.output.see(tk.END)
        except:
            pass # Ignore errors if window is closed

    def flush(self):
        pass

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Teacher WebDAV Manager")
        self.root.geometry("500x650")
        
        # Load Config
        self.config = {}
        self.load_config_file()

        # UI Elements
        self.create_widgets()
        
        # Redirect stdout/stderr for MAIN process (GUI logic logs)
        sys.stdout = RedirectText(self.log_area, self.root)
        sys.stderr = RedirectText(self.log_area, self.root)

        self.server_process = None
        self.log_queue = multiprocessing.Queue()
        self.poll_log_queue()

    def poll_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_area.insert(tk.END, msg)
                self.log_area.see(tk.END)
        except queue.Empty:
            pass
        # Poll every 100ms
        self.root.after(100, self.poll_log_queue)

    def load_config_file(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "host": "0.0.0.0",
                "port": 8080,
                "upload_folder": "data",
                "debug": True,
                "admin_user": "admin",
                "admin_pass": "123456",
                "secret_key": "changeme"
            }

    def save_config_file(self):
        self.config['host'] = self.host_var.get()
        try:
            self.config['port'] = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Port must be a number")
            return False
        
        self.config['admin_user'] = self.user_var.get()
        self.config['admin_pass'] = self.pass_var.get()
        self.config['upload_folder'] = self.folder_var.get()

        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)
        
        reload_config()
        return True

    def get_lan_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def create_widgets(self):
        # Settings Frame
        settings_frame = ttk.LabelFrame(self.root, text="Server Settings", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Host
        ttk.Label(settings_frame, text="Host IP:").grid(row=0, column=0, sticky="w", pady=5)
        self.host_var = tk.StringVar(value=self.config.get('host', '0.0.0.0'))
        ttk.Entry(settings_frame, textvariable=self.host_var).grid(row=0, column=1, sticky="ew", pady=5)

        # Port
        ttk.Label(settings_frame, text="Port:").grid(row=1, column=0, sticky="w", pady=5)
        self.port_var = tk.StringVar(value=str(self.config.get('port', 8080)))
        ttk.Entry(settings_frame, textvariable=self.port_var).grid(row=1, column=1, sticky="ew", pady=5)

        # Admin User
        ttk.Label(settings_frame, text="Admin User:").grid(row=2, column=0, sticky="w", pady=5)
        self.user_var = tk.StringVar(value=self.config.get('admin_user', 'admin'))
        ttk.Entry(settings_frame, textvariable=self.user_var).grid(row=2, column=1, sticky="ew", pady=5)

        # Admin Pass
        ttk.Label(settings_frame, text="Admin Pass:").grid(row=3, column=0, sticky="w", pady=5)
        self.pass_var = tk.StringVar(value=self.config.get('admin_pass', '123456'))
        ttk.Entry(settings_frame, textvariable=self.pass_var, show="*").grid(row=3, column=1, sticky="ew", pady=5)
        
        # Upload Folder
        ttk.Label(settings_frame, text="Folder chứa bài:").grid(row=4, column=0, sticky="w", pady=5)
        self.folder_var = tk.StringVar(value=self.config.get('upload_folder', 'data'))
        folder_entry = ttk.Entry(settings_frame, textvariable=self.folder_var)
        folder_entry.grid(row=4, column=1, sticky="ew", pady=5)
        ttk.Button(settings_frame, text="Chọn...", command=self.choose_folder).grid(row=4, column=2, padx=2)
        ttk.Button(settings_frame, text="Mở HS", command=self.open_folder).grid(row=4, column=3, padx=2)

        settings_frame.columnconfigure(1, weight=1)

        # Buttons Frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.start_btn = ttk.Button(btn_frame, text="Start Server", command=self.start_server)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=2)

        self.stop_btn = ttk.Button(btn_frame, text="Stop Server", command=self.stop_server, state="disabled")
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=2)
        
        self.browser_btn = ttk.Button(btn_frame, text="Mở Web", command=self.open_browser, state="disabled")
        self.browser_btn.pack(side="left", expand=True, fill="x", padx=2)

        self.exit_btn = ttk.Button(btn_frame, text="Exit", command=self.exit_app)
        self.exit_btn.pack(side="left", expand=True, fill="x", padx=2)

        # Log Area
        log_frame = ttk.LabelFrame(self.root, text="Console Log", padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, height=10, state='normal', font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True)

    def choose_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_var.set(folder_selected)

    def open_folder(self):
        folder = self.folder_var.get()
        # If relative path, make it absolute based on CWD or executable loc
        if not os.path.isabs(folder):
            # In compiled exe, CWD might not be where the exe is, but usually it is.
            # safe logic:
            if getattr(sys, 'frozen', False):
                base = os.path.dirname(sys.executable)
            else:
                base = os.path.abspath(os.path.dirname(__file__))
            folder = os.path.join(base, folder)

        if os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
        else:
            try:
                os.makedirs(folder, exist_ok=True)
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Error", f"Folder does not exist and cannot act: {e}")

    def start_server(self):
        if self.server_process and self.server_process.is_alive():
            messagebox.showinfo("Info", "Server is already running.")
            return

        if self.save_config_file():
            print("Config saved. Starting server...")
            host = self.config.get('host', '0.0.0.0')
            port = self.config.get('port', 8080)
            
            # Use multiprocessing Process instead of Thread
            self.server_process = multiprocessing.Process(
                target=run_waitress_server, 
                args=(host, port, self.log_queue),
                daemon=True
            )
            self.server_process.start()
            
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.browser_btn.config(state="normal")
            
            # Print info (from main process)
            print(f"GUI: Server process started on http://{host}:{port}")
            print(f"GUI: Folder: {self.config.get('upload_folder')}")

            # Show helpful IP info
            lan_ip = self.get_lan_ip()
            print(f"--------------------------------------------------")
            print(f"HƯỚNG DẪN HỌC SINH:")
            print(f"Truy cập địa chỉ: http://{lan_ip}:{port}")
            print(f"--------------------------------------------------")

    def stop_server(self):
        if not self.server_process or not self.server_process.is_alive():
            return
            
        self.stop_btn.config(text="Stopping...", state="disabled")
        
        # Terminate the process
        try:
            self.server_process.terminate()
            self.server_process.join(timeout=2)
            if self.server_process.is_alive():
                 self.server_process.kill()
            print("GUI: Server process terminated.")
        except Exception as e:
            print(f"GUI: Error stopping server: {e}")
            
        self.server_process = None
        
        self.start_btn.config(state="normal")
        self.stop_btn.config(text="Stop Server", state="disabled")
        self.browser_btn.config(state="disabled")

    def _shutdown_task(self):
        # Legacy thread task - not used with multiprocessing
        pass

    def _on_server_stopped(self):
        # Legacy callback - not used with multiprocessing
        pass
        
    def open_browser(self):
        port = self.config.get('port', 8080)
        webbrowser.open(f"http://localhost:{port}")

    def exit_app(self):
        if self.server_process and self.server_process.is_alive():
            self.stop_server()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    multiprocessing.freeze_support() # Crucial for PyInstaller
    try:
        root = tk.Tk()
        app_gui = AppGUI(root)
        root.mainloop()
    except Exception as e:
        # Fallback if GUI fails
        with open("error.log", "w") as f:
            f.write(str(e))
