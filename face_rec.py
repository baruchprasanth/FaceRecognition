from flask import Flask, render_template, request, jsonify
import face_recognition
import base64
import numpy as np
from PIL import Image
import io
import json
import os
import socket

app = Flask(__name__, template_folder='templates')

# Ensure the 'users' directory exists
if not os.path.exists('users'):
    os.makedirs('users')

# Find Free ports
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

# Load existing users
def load_users():
    if os.path.exists('users/users.json'):
        with open('users/users.json', 'r') as f:
            return json.load(f)
    return {}

# Save users
def save_users(users):
    with open('users/users.json', 'w') as f:
        json.dump(users, f)

users = load_users()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture', methods=['POST'])
def capture():
    image_data = request.json['image']
    # Remove the "data:image/jpeg;base64," part
    image_data = image_data.split(',')[1]
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
    
    # Convert image to RGB (face_recognition requires RGB)
    rgb_image = image.convert('RGB')
    
    # Convert PIL Image to numpy array
    np_image = np.array(rgb_image)
    
    # Use face_recognition to find faces
    face_locations = face_recognition.face_locations(np_image)
    if len(face_locations) == 0:
        return jsonify({"error": "No face detected in the image"}), 400
    
    # Use face_recognition to get face encodings
    face_encodings = face_recognition.face_encodings(np_image, face_locations)
    if len(face_encodings) == 0:
        return jsonify({"error": "Could not encode the face"}), 400

    return jsonify({"message": "Face captured successfully", "encoding": face_encodings[0].tolist()})

@app.route('/register', methods=['POST'])
def register():
    user_id = request.json['userId']
    face_encoding = request.json['faceEncoding']
    
    if user_id in users:
        return jsonify({"error": "User ID already exists"}), 400
    
    users[user_id] = face_encoding
    save_users(users)
    return jsonify({"message": f"User {user_id} registered successfully"})

@app.route('/login', methods=['POST'])
def login():
    unknown_encoding = np.array(request.json['faceEncoding'])
    
    for user_id, stored_encoding in users.items():
        stored_encoding = np.array(stored_encoding)
        # Use face_recognition to compare faces
        matches = face_recognition.compare_faces([stored_encoding], unknown_encoding)
        if matches[0]:
            return jsonify({"message": f"Login successful for user {user_id}"})
    
    return jsonify({"error": "Face not recognized"}), 401

if __name__ == '__main__':
    port = find_free_port()
    print(f"Running on http://127.0.0.1:{port}")
    app.run(debug=True, port=port)