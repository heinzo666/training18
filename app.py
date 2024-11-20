# First, run these commands in separate cells:
# !pip install flask-ngrok pyngrok pillow
# !ngrok authtoken YOUR_NGROK_TOKEN  # Replace with your ngrok token
# !git clone YOUR_GITHUB_REPO_URL    # Replace with your repo URL

import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image
import hashlib
from urllib.parse import urlparse
from flask_ngrok import run_with_ngrok
from pyngrok import ngrok

app = Flask(__name__)
run_with_ngrok(app)

# Assuming your GitHub repo is cloned to /content/your-repo-name
# Replace 'your-repo-name' with your actual repository name
REPO_PATH = "/content/your-repo-name"  # Update this with your repo name

# Set up paths relative to the repository
def setup_directories():
    directories = {
        'json': os.path.join(REPO_PATH, "json"),
        'media': os.path.join(REPO_PATH, "media"),
        'templates': os.path.join(REPO_PATH, "templates"),
        'avatar': os.path.join(REPO_PATH, "avatar")
    }
    return directories

# Initialize directories
DIRS = setup_directories()

def get_media_path(channel_id):
    return os.path.join(DIRS['media'], channel_id)

def load_json_files_with_channel():
    messages = []
    json_dir = DIRS['json']
    
    if not os.path.exists(json_dir):
        print(f"Warning: JSON directory not found at {json_dir}")
        return messages
        
    for filename in os.listdir(json_dir):
        if filename.endswith('.json'):
            with open(os.path.join(json_dir, filename), 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    for item in data:
                        content = item.get('content')
                        timestamp = item.get('timestamp')
                        channel_id = item.get('channel_id')
                        dt = datetime.fromisoformat(timestamp) if timestamp else None
                        date_str = dt.strftime("%Y-%m-%d") if dt else None

                        if item.get('attachments'):
                            for attachment in item['attachments']:
                                url = attachment.get('url')
                                messages.append((content, url, date_str, dt, channel_id))
                        else:
                            messages.append((content, None, date_str, dt, channel_id))
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {filename}: {e}")
    return messages

def filter_messages(start_date, end_date, selected_channel, media_type):
    messages = load_json_files_with_channel()
    filtered_messages = []

    start_datetime = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)

    for content, url, date_str, dt, channel_id in messages:
        if dt is not None and start_datetime <= dt <= end_datetime:
            if selected_channel == "All" or channel_id == selected_channel:
                message_media_type = "text"
                if url:
                    parsed_url = urlparse(url)
                    path = parsed_url.path
                    url_extension = os.path.splitext(path)[1]
                    url_hash = hashlib.md5(url.encode()).hexdigest()
                    media_path = get_media_path(channel_id)
                    
                    if url_extension.lower() == '.mp3':
                        file_path = os.path.join(media_path, f"{url_hash}.mp3")
                        if os.path.exists(file_path):
                            url = f"/media/{channel_id}/{url_hash}.mp3"
                            message_media_type = "audio"
                        else:
                            message_media_type = "unknown"
                    elif url_extension.lower() == '.m4a':
                        file_path = os.path.join(media_path, f"{url_hash}.mp3")
                        if os.path.exists(file_path):
                            url = f"/media/{channel_id}/{url_hash}.mp3"
                            message_media_type = "audio"
                        else:
                            message_media_type = "unknown"
                    else:
                        for ext in ['.jpg', '.png', '.gif']:
                            file_path = os.path.join(media_path, f"{url_hash}{ext}")
                            if os.path.exists(file_path):
                                url = f"/media/{channel_id}/{url_hash}{ext}"
                                message_media_type = "image"
                                break
                        else:
                            message_media_type = "unknown"
                
                if media_type == "all" or media_type == message_media_type:
                    filtered_messages.append((content, url, date_str, dt.isoformat(), channel_id, message_media_type))

    return sorted(filtered_messages, key=lambda x: x[3])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_messages', methods=['POST'])
def get_messages():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    selected_channel = request.form.get('channel')
    media_type = request.form.get('media_type')
    messages = filter_messages(start_date, end_date, selected_channel, media_type)
    return jsonify(messages)

@app.route('/media/<path:channel_id>/<path:filename>')
def serve_image(channel_id, filename):
    media_path = get_media_path(channel_id)
    return send_from_directory(media_path, filename)

@app.route('/avatar/<filename>')
def serve_avatar(filename):
    return send_from_directory(DIRS['avatar'], filename)

if __name__ == '__main__':
    print("Starting Flask application...")
    print(f"Using repository path: {REPO_PATH}")
    
    # Verify directories exist
    for dir_name, dir_path in DIRS.items():
        if not os.path.exists(dir_path):
            print(f"Warning: {dir_name} directory not found at {dir_path}")
    
    app.run()