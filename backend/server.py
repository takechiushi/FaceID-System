from flask import Flask, request, jsonify, send_from_directory
from bson.objectid import ObjectId
import shutil
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

# 1. API LẤY DANH SÁCH NHÂN VIÊN
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        # Lấy tất cả user từ MongoDB, sắp xếp người mới nhất lên đầu
        users = list(face_system.users_col.find().sort("created_at", -1))
        
        # Xử lý dữ liệu trước khi trả về (Convert ObjectId thành String)
        for user in users:
            user['_id'] = str(user['_id'])
            # Tạo đường dẫn ảnh avatar chuẩn cho Frontend
            if 'avatar' in user:
                # Thay thế dấu \ thành / để chạy trên web
                clean_path = user['avatar'].replace('\\', '/')
                if 'static/uploads/' in clean_path:
                    clean_path = clean_path.split('static/uploads/')[1]
                user['avatar'] = f"static/uploads/{clean_path}"
        
        return jsonify(users)
    except Exception as e:
        print(e)
        return jsonify([]), 500

# 2. API XÓA NHÂN VIÊN
@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        # Tìm user để lấy tên thư mục ảnh trước khi xóa
        user = face_system.users_col.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        # 1. Xóa trong Collection Users
        face_system.users_col.delete_one({"_id": ObjectId(user_id)})
        
        # 2. Xóa trong Collection Vectors (Quan trọng: Xóa đặc trưng khuôn mặt)
        face_system.vectors_col.delete_many({"user_id": user_id})
        
        # 3. Xóa thư mục ảnh trên ổ cứng (Cho sạch máy)
        user_folder = os.path.join(UPLOAD_FOLDER, user['name'])
        if os.path.exists(user_folder):
            try:
                shutil.rmtree(user_folder) # Xóa cả thư mục
            except:
                pass

        # 4. Reload lại model KNN để cập nhật thay đổi ngay lập tức
        face_system.reload_model()
        
        return jsonify({"success": True, "message": "Đã xóa thành công"})
    except Exception as e:
        print(f"Lỗi xóa: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    
# 3. API ĐĂNG KÝ NHÂN VIÊN MỚI
@app.route('/api/register', methods=['POST'])
def register():
    try:
        name = request.form.get('name')
        age = request.form.get('age')
        role = request.form.get('role', 'user') # Mặc định là user
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        # Nhận 5 ảnh từ FormData
        files = request.files.getlist('files')

        if not files or len(files) == 0:
            return jsonify({"success": False, "message": "Chưa chọn ảnh nào!"}), 400
        
        # Tạo thư mục lưu ảnh
        user_dir = os.path.join(UPLOAD_FOLDER, name)
        # Nếu thư mục đã tồn tại (ví dụ đăng ký đè), ta có thể xóa cũ hoặc giữ nguyên
        # Ở đây tôi chọn giữ nguyên và ghi đè ảnh
        os.makedirs(user_dir, exist_ok=True)

        saved_paths = []
        
        user_dir = os.path.join(UPLOAD_FOLDER, name)
        os.makedirs(user_dir, exist_ok=True)
        
        # 3. Lưu từng file
        for i, file in enumerate(files):
            if file:
                # Đặt tên file đơn giản: 0.jpg, 1.jpg, 2.jpg...
                # Hoặc giữ nguyên tên gốc: filename = file.filename
                filename = f"{i}.jpg" 
                path = os.path.join(user_dir, filename)
                file.save(path)
                saved_paths.append(path)
        
        if len(saved_paths) < 1:
            return jsonify({"success": False, "message": "Lỗi lưu file"}), 400

        user_id = face_system.register_user(name, age, saved_paths, role, username, password)
        
        if user_id:
            return jsonify({"success": True, "message": "Đăng ký thành công!"})
        else:
            # Nếu Core AI không tìm thấy mặt, xóa thư mục vừa tạo cho sạch rác
            import shutil
            shutil.rmtree(user_dir)
            return jsonify({"success": False, "message": "Không tìm thấy khuôn mặt trong ảnh, vui lòng chọn ảnh rõ hơn."}), 400

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 4. API NHẬN DIỆN KHUÔN MẶT
@app.route('/api/recognize', methods=['POST'])
def recognize():
    try:
        img = None

        # TRƯỜNG HỢP 1: Nhận file từ FormData (VueJS đang gửi cái này)
        if 'file' in request.files:
            file = request.files['file']
            # Đọc byte trực tiếp từ file upload mà không cần base64 decode
            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        # TRƯỜNG HỢP 2: Nhận Base64 JSON (Dự phòng cho code cũ nếu còn dùng)
        elif request.is_json and 'image' in request.json:
            data = request.json
            image_data = data.get('image')
            header, encoded = image_data.split(",", 1)
            nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        else:
            return jsonify({"success": False, "message": "Dữ liệu không hợp lệ (Cần FormData hoặc JSON Base64)"}), 400

        # Nếu decode thất bại
        if img is None:
            return jsonify({"success": False, "message": "Ảnh bị lỗi, không đọc được"}), 400

        # Lưu tạm ảnh xuống ổ cứng để Core AI đọc
        # (Vì Core AI của bạn đang thiết kế để đọc từ đường dẫn file)
        temp_path = "temp_login.jpg"
        cv2.imwrite(temp_path, img)
        
        # Gọi Core AI nhận diện
        user = face_system.recognize(temp_path)
        
        if user:
            # Tạo URL avatar hiển thị
            user['avatar_url'] = f"http://localhost:5000/{user['avatar'].replace(os.sep, '/')}"
            return jsonify({"success": True, "found": True, "user": user})
        else:
            return jsonify({"success": False, "message": "Không nhận diện được hoặc người lạ"}), 200 # Trả về 200 để Frontend không báo lỗi đỏ, chỉ báo không tìm thấy
            
    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"success": False, "message": "Lỗi xử lý server"}), 500

# 5. API ĐĂNG NHẬP ADMIN
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Tìm trong DB xem có ông admin nào trùng user/pass không
    user = face_system.users_col.find_one({
        "role": "admin", 
        "username": username, 
        "password": password
    })

    if user:
        return jsonify({
            "success": True, 
            "msg": "Chào sếp!", 
            "user": {
                "name": user['name'],
                "role": user['role']
            }
        })
    else:
        return jsonify({"success": False, "msg": "Sai tài khoản hoặc không phải Admin!"}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5000)