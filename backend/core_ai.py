from datetime import datetime
import numpy as np
import cv2
import os
from insightface.app import FaceAnalysis
from sklearn.preprocessing import normalize
from sklearn.neighbors import KNeighborsClassifier
from pymongo import MongoClient
from bson.objectid import ObjectId

class FaceSystem:
    def __init__(self):
        # Kết nối Mongo
        self.client = MongoClient("mongodb://127.0.0.1:27017/")
        self.db = self.client["FaceDB"]
        self.users_col = self.db["users"]
        self.vectors_col = self.db["vectors"]
        
        # Load ArcFace
        print("⏳ Đang tải ArcFace...")
        self.app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        
        self.knn = None
        self.reload_model()

    def get_embedding(self, img_path):
        try:
            # 1. Đọc file vào mảng byte bằng thư viện chuẩn Python (hỗ trợ Unicode)
            with open(img_path, "rb") as f:
                file_bytes = bytearray(f.read())
                numpy_array = np.asarray(file_bytes, dtype=np.uint8)
            # 2. Decode mảng byte thành ảnh OpenCV
            img = cv2.imdecode(numpy_array, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"Lỗi đọc file {img_path}: {e}")
            return None
        # -----------------------------------

        if img is None: 
            print(f"Không đọc được ảnh: {img_path}")
            return None

        faces = self.app.get(img)
        if len(faces) == 0: return None
        
        main_face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
        return main_face.embedding

    def reload_model(self):
        data = list(self.vectors_col.find())
        if len(data) == 0:
            self.knn = None
            return
        # --- CẢI TIẾN 1: Chuẩn hóa dữ liệu đầu vào ---
        X_raw = [np.array(d['vector']) for d in data]
        
        # L2 Normalize: Giúp thuật toán Cosine hoạt động ổn định hơn rất nhiều
        X = normalize(X_raw, norm='l2')
        # X = [d['vector'] for d in data]
        y = [d['user_id'] for d in data]
        
        n_neighbors = min(3, len(X))
        self.knn = KNeighborsClassifier(n_neighbors=n_neighbors, metric='cosine')
        self.knn.fit(X, y)
        print("✅ KNN đã cập nhật!")

    def register_user(self, name, age, img_paths, role="user", username=None, password=None):
        
        # Tạo document user
        user_doc = {
            "name": name,
            "age": age,
            "avatar": img_paths[0],
            "role": role,          # "admin" hoặc "user"
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Nếu là Admin thì bắt buộc phải có username/password để đăng nhập trang quản trị
        if role == "admin":
            if not username or not password:
                print("❌ Admin phải có username và password!")
                return None
            user_doc["username"] = username
            user_doc["password"] = password # Lưu ý: Thực tế phải mã hóa (Hash), nhưng demo ta lưu text trần tạm nhé.

        # 1. Lưu User vào Mongo
        user_id = self.users_col.insert_one(user_doc).inserted_id
        
        # 2. Lưu Vectors (Phần này giữ nguyên)
        count = 0
        for path in img_paths:
            emb = self.get_embedding(path)
            if emb is not None:
                self.vectors_col.insert_one({
                    "user_id": str(user_id),
                    "vector": emb.tolist()
                })
                count += 1
        
        if count > 0:
            self.reload_model()
            return str(user_id)
        else:
            self.users_col.delete_one({"_id": user_id})
            return None

    def recognize(self, img_path, threshold=0.55):
        if self.knn is None: return None
        
        emb = self.get_embedding(img_path)
        if emb is None: return None

        input_vec = np.array(emb).reshape(1, -1)
        input_vec = normalize(input_vec, norm='l2')
        distances, _ = self.knn.kneighbors(input_vec, n_neighbors=1)
        # --- CẢI TIẾN 4: In ra Log để Debug ---
        # Đây là dòng quan trọng nhất giúp bạn biết tại sao bị từ chối
        print(f"🔍 Khoảng cách (Distance): {distances[0][0]:.4f} | Ngưỡng: {threshold}")

        if distances[0][0] > threshold: # Ngưỡng
            print(f"   -> BỊ TỪ CHỐI (Do > {threshold})")
            return None
        
        user_id = self.knn.predict(input_vec)[0]
        user = self.users_col.find_one({"_id": ObjectId(user_id)})
        
        # Convert ObjectId to string for JSON
        if user: 
            user['_id'] = str(user['_id'])
            return user
        return None