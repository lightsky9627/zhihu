import os
import random
import string
import logging
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from database import init_db, get_stats, increment_stats, get_config, set_config
from zhihu_core import ZhihuDownloader
import threading

app = Flask(__name__)
# Generate a random secret key for session management
app.secret_key = os.urandom(24)

# Configure locking for thread-safe stats updates
stats_lock = threading.Lock()

# Admin Password Configuration
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    # Generate random password if not set
    chars = string.ascii_letters + string.digits
    ADMIN_PASSWORD = ''.join(random.choice(chars) for _ in range(12))
    print(f"\n{'='*40}")
    print(f"ADMIN PASSWORD: {ADMIN_PASSWORD}")
    print(f"{'='*40}\n")

# Initialize Database
init_db()

@app.route('/')
def index():
    stats = get_stats()
    # Increment total visitors and daily visitors logic would go here ideally 
    # but for simplicity we'll just show current stats
    return render_template('index.html', stats=stats)

@app.route('/api/stats/visit', methods=['POST'])
def track_visit():
    with stats_lock:
        visitor_info = increment_stats(visit=True)
    return jsonify(visitor_info)

@app.route('/api/download', methods=['POST'])
def download():
    url = request.form.get('url')
    user_cookie = request.form.get('cookie')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    # Priority: User Cookie > Global Cookie
    cookie_to_use = user_cookie
    if not cookie_to_use:
        global_cookie = get_config('global_cookie')
        if global_cookie:
            cookie_to_use = global_cookie
    
    downloader = ZhihuDownloader(cookie=cookie_to_use)
    
    try:
        # returns (filename, content_bytes)
        filename, content = downloader.download(url)
        
        with stats_lock:
            increment_stats(download=True)
            
        # Create a generator or save to temp file? 
        # For simplicity and docker ephemeral nature, let's use BytesIO or temp file
        # But wait, zhihu_core might save assets too (images).
        # We need a proper way to zip the result if it has images, 
        # OR just return the markdown if it uses remote images (which zhihu core usually downloads).
        # If the core downloads images, we should zip the folder.
        
        # Let's assume zhihu_core handles zipping or we do it here.
        # For this version, let's stick to returning the markdown file provided 
        # and assume images are inline base64 or external (or we adapt core to zip).
        # Given "just markdown" request, creating a zip is safer.
        
        return send_file(
            content,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip' # or text/markdown depending on impl
        )
    except Exception as e:
         return jsonify({'error': str(e)}), 500

# --- Admin Routes ---

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid Password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/api/admin/cookie', methods=['POST'])
def update_cookie():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    new_cookie = request.form.get('cookie')
    if not new_cookie:
        return jsonify({'error': 'Cookie is required'}), 400
        
    set_config('global_cookie', new_cookie)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
