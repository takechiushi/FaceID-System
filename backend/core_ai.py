import numpy as np
import cv2
import os
from insightface.app import FaceAnalysis
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
        
        X = [d['vector'] for d in data]
        y = [d['user_id'] for d in data]
        
        n_neighbors = min(3, len(X))
        self.knn = KNeighborsClassifier(n_neighbors=n_neighbors, metric='cosine')
        self.knn.fit(X, y)
        print("✅ KNN đã cập nhật!")

    def register_user(self, name, age, img_paths):
        # 1. Lưu User
        user_id = self.users_col.insert_one({
            "name": name,
            "age": age,
            "avatar": img_paths[0] # Lấy ảnh đầu tiên làm avatar
        }).inserted_id
        
        # 2. Lưu Vectors
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

    def recognize(self, img_path):
        if self.knn is None: return None
        
        emb = self.get_embedding(img_path)
        if emb is None: return None
        
        input_vec = np.array(emb).reshape(1, -1)
        distances, _ = self.knn.kneighbors(input_vec, n_neighbors=1)
        
        if distances[0][0] > 0.5: # Ngưỡng
            return None
        
        user_id = self.knn.predict(input_vec)[0]
        user = self.users_col.find_one({"_id": ObjectId(user_id)})
        
        # Convert ObjectId to string for JSON
        if user: 
            user['_id'] = str(user['_id'])
            return user
        return None