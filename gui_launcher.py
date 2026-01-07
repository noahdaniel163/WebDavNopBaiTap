import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import threading
import sys
import os
import webbrowser
import logging
import requests
from waitress import serve
from app import app, reload_config, CONFIG_FILE

class ServerThread(threading.Thread):
    def __init__(self, host, port, debug):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.debug = debug
        self.daemon = True

    def run(self):
        # Disable Flask reloader to avoid main thread errors in GUI
        try:
            # Use Waitress for production-ready performance suitable for 60+ users
            # threads=16 allows 16 concurrent requests processing (good for file uploads)
            print(f"Starting Waitress server with 16 threads...")
            serve(app, host=self.host, port=self.port, threads=16) 
        except Exception as e:
            print(f"Error starting server: {e}")

class RedirectText:
    def __init__(self, text_ctrl):
        self.output = text_ctrl

    def write(self, string):
        self.output.insert(tk.END, string)
        self.output.see(tk.END)

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
        
        # Redirect stdout/stderr
        sys.stdout = RedirectText(self.log_area)
        sys.stderr = RedirectText(self.log_area)

        self.server_thread = None

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
        ttk.Button(settings_frame, text="Chọn Folder", command=self.choose_folder).grid(row=4, column=2, padx=5)

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

    def start_server(self):
        if self.server_thread and self.server_thread.is_alive():
            messagebox.showinfo("Info", "Server is already running.")
            return

        if self.save_config_file():
            print("Config saved. Starting server...")
            host = self.config.get('host', '0.0.0.0')
            port = self.config.get('port', 8080)
            
            self.server_thread = ServerThread(host, port, self.config.get('debug', False))
            self.server_thread.start()
            
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.browser_btn.config(state="normal")
            
            # Print info
            print(f"Server started on http://{host}:{port}")
            print(f"Folder: {self.config.get('upload_folder')}")

    def stop_server(self):
        if not self.server_thread or not self.server_thread.is_alive():
            return
            
        host = self.config.get('host', '0.0.0.0')
        if host == "0.0.0.0":
             host = "127.0.0.1" 
             
        port = self.config.get('port', 8080)
        try:
            # Send shutdown request to the server
            requests.post(f"http://{host}:{port}/shutdown")
            self.server_thread.join(timeout=2)
            print("Server stopped.")
        except Exception as e:
            print(f"Error stopping server: {e}")
            
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.browser_btn.config(state="disabled")

    def open_browser(self):
        port = self.config.get('port', 8080)
        webbrowser.open(f"http://localhost:{port}")

    def exit_app(self):
        if self.server_thread and self.server_thread.is_alive():
            self.stop_server()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app_gui = AppGUI(root)
        root.mainloop()
    except Exception as e:
        # Fallback if GUI fails
        with open("error.log", "w") as f:
            f.write(str(e))
