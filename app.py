import os
import json
import sys
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

# Determine if running as a script or frozen exe
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    # Templates are bundled inside the exe (in sys._MEIPASS)
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    # Config and data should be relative to the executable file
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as python script
    template_folder = 'templates'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load configuration from file next to the executable/script
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

# Create default config if missing
if not os.path.exists(CONFIG_FILE):
    default_config = {
        "host": "0.0.0.0",
        "port": 8080,
        "upload_folder": "data",
        "debug": True,
        "admin_user": "admin",
        "admin_pass": "123456",
        "secret_key": "change_this_secret_key"
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=4)

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

app = Flask(__name__, template_folder=template_folder)
app.secret_key = config.get('secret_key', 'default_secret_key')

def get_upload_folder():
    folder_name = config.get('upload_folder', 'data')
    folder_path = os.path.join(BASE_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def reload_config():
    global config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            new_config = json.load(f)
            config.clear()
            config.update(new_config)
            app.secret_key = config.get('secret_key', 'default_secret_key')

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('index.html', logged_in=False)
    
    upload_folder = get_upload_folder()
    if os.path.exists(upload_folder):
        files = os.listdir(upload_folder)
        files.sort()
    else:
        files = []
    return render_template('index.html', files=files, logged_in=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == config.get('admin_user', 'admin') and password == config.get('admin_pass', '123456'):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Sai tên đăng nhập hoặc mật khẩu!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
        
    if file:
        filename = secure_filename(file.filename)
        upload_folder = get_upload_folder()
        
        # Handle duplicate filenames
        name, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(os.path.join(upload_folder, filename)):
            filename = f"{name}_{counter:02d}{ext}"
            counter += 1
            
        file.save(os.path.join(upload_folder, filename))
        flash(f'Nộp file thành công: {filename}')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return send_from_directory(get_upload_folder(), filename)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    file_path = os.path.join(get_upload_folder(), filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f'Đã xóa file: {filename}')
    return redirect(url_for('index'))

@app.route('/shutdown', methods=['POST'])
def shutdown():
    # Only allow shutdown from localhost for security
    if request.remote_addr not in ['127.0.0.1', '::1']:
        return "Forbidden", 403
    
    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    if shutdown_func is None:
        return "Not running with the Werkzeug Server", 500
    
    shutdown_func()
    return 'Server shutting down...'
