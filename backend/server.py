from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
import numpy as np
import cv2
from core_ai import FaceSystem

app = Flask(__name__)
CORS(app) # Cho phép Vuejs gọi API

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

face_system = FaceSystem()

# API để Vuejs hiển thị ảnh avatar
@app.route('/static/uploads/<path:filename>')
def serve_static(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/register', methods=['POST'])
def register():
    try:
        name = request.form.get('name')
        age = request.form.get('age')
        
        # Nhận 5 ảnh từ FormData
        angles = ['straight', 'up', 'left', 'right', 'down']
        saved_paths = []
        
        user_dir = os.path.join(UPLOAD_FOLDER, name)
        os.makedirs(user_dir, exist_ok=True)
        
        for angle in angles:
            file = request.files.get(angle)
            if file:
                path = os.path.join(user_dir, f"{angle}.jpg")
                file.save(path)
                saved_paths.append(path)
        
        if len(saved_paths) < 5:
            return jsonify({"success": False, "message": "Thiếu ảnh!"}), 400

        user_id = face_system.register_user(name, age, saved_paths)
        
        if user_id:
            return jsonify({"success": True, "message": "Đăng ký thành công!"})
        else:
            return jsonify({"success": False, "message": "Không tìm thấy mặt trong ảnh"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        # Nhận ảnh base64 từ webcam hoặc file upload
        data = request.json
        image_data = data.get('image') # Chuỗi base64
        
        # Decode Base64 -> Image
        header, encoded = image_data.split(",", 1)
        nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        temp_path = "temp_login.jpg"
        cv2.imwrite(temp_path, img)
        
        user = face_system.recognize(temp_path)
        
        if user:
            # Tạo URL đầy đủ cho avatar để Vue hiển thị
            user['avatar_url'] = f"http://localhost:5000/{user['avatar'].replace(os.sep, '/')}"
            return jsonify({"success": True, "user": user})
        else:
            return jsonify({"success": False, "message": "Không nhận diện được hoặc người lạ"}), 401
            
    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": "Lỗi server"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)