import os
import shutil
import cv2
import numpy as np
import random
from pymongo import MongoClient
from insightface.app import FaceAnalysis
from tqdm import tqdm # Thư viện thanh tiến trình (pip install tqdm)

# --- CẤU HÌNH ĐƯỜNG DẪN (BẠN SỬA LẠI CHO ĐÚNG) ---
# 1. Đường dẫn đến thư mục chứa dữ liệu VGGFace2 trên máy bạn
VGGFACE_ROOT = r"D:\1.Study\1.Caohoc\K37\1.ML\1.CODE\BTCK\VGGFace2\VGGFace2_Filtered" 

# 2. Số lượng người muốn thêm
NUM_PEOPLE = 480 

# 3. Đường dẫn thư mục uploads của Backend (để copy avatar sang cho Web hiện)
BACKEND_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")

# --- KẾT NỐI DB & MODEL ---
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["FaceDB"]
users_col = db["users"]
vectors_col = db["vectors"]

print("⏳ Đang khởi tạo ArcFace...")
app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

def get_embedding(img_path):
    """Hàm đọc ảnh và lấy vector (hỗ trợ đường dẫn Windows)"""
    try:
        with open(img_path, "rb") as f:
            file_bytes = bytearray(f.read())
            numpy_array = np.asarray(file_bytes, dtype=np.uint8)
        img = cv2.imdecode(numpy_array, cv2.IMREAD_COLOR)
        
        if img is None: return None
        
        faces = app.get(img)
        if len(faces) == 0: return None
        # Lấy mặt to nhất
        main_face = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
        return main_face.embedding
    except Exception:
        return None

def seed_database():
    if not os.path.exists(VGGFACE_ROOT):
        print(f"❌ Lỗi: Không tìm thấy thư mục VGGFace2 tại: {VGGFACE_ROOT}")
        return

    # Lấy danh sách thư mục con (mỗi thư mục là 1 người)
    all_folders = [d for d in os.listdir(VGGFACE_ROOT) if os.path.isdir(os.path.join(VGGFACE_ROOT, d))]
    
    # Chỉ lấy số lượng yêu cầu
    selected_folders = all_folders[:NUM_PEOPLE]
    
    print(f"🚀 Bắt đầu nạp {len(selected_folders)} người vào hệ thống...")

    count_success = 0
    
    # Dùng tqdm để hiện thanh phần trăm cho chuyên nghiệp
    for person_id in tqdm(selected_folders):
        person_path = os.path.join(VGGFACE_ROOT, person_id)
        
        # Lấy tất cả ảnh jpg trong folder đó
        images = [f for f in os.listdir(person_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # Cần ít nhất 1 ảnh để làm avatar và training
        if len(images) < 1: continue
        
        # Lấy tối đa 5 ảnh để trích xuất vector
        process_images = images[:5]
        
        # --- BƯỚC 1: XỬ LÝ AVATAR CHO WEB ---
        # Giả lập tên người dùng (VD: User n000123)
        user_name = f"User {person_id}"
        user_age = random.randint(20, 60) # Random tuổi
        
        # Tạo thư mục trong static/uploads để Vuejs load được ảnh
        dest_folder = os.path.join(BACKEND_UPLOAD_DIR, person_id)
        os.makedirs(dest_folder, exist_ok=True)
        
        # Copy ảnh đầu tiên làm avatar
        avatar_src = os.path.join(person_path, process_images[3])
        avatar_dst = os.path.join(dest_folder, process_images[3])
        shutil.copy2(avatar_src, avatar_dst)
        
        # Đường dẫn tương đối để lưu vào DB (Backend API sẽ phục vụ file này)
        # Lưu ý: dùng dấu gạch chéo / cho chuẩn web
        db_avatar_path = f"static/uploads/{person_id}/{process_images[3]}"

        # --- BƯỚC 2: INSERT USER VÀO MONGODB ---
        user_doc = {
            "name": user_name,
            "role": "user",
            "age": user_age,
            "avatar": db_avatar_path
        }
        insert_result = users_col.insert_one(user_doc)
        user_id_obj = insert_result.inserted_id
        
        # --- BƯỚC 3: TRÍCH XUẤT VÀ INSERT VECTOR ---
        vectors_added = 0
        for img_name in process_images:
            full_img_path = os.path.join(person_path, img_name)
            emb = get_embedding(full_img_path)
            
            if emb is not None:
                vectors_col.insert_one({
                    "user_id": str(user_id_obj),
                    "vector": emb.tolist()
                })
                vectors_added += 1
        
        # Nếu không trích xuất được vector nào (ảnh lỗi hết), xóa user đó đi cho sạch DB
        if vectors_added == 0:
            users_col.delete_one({"_id": user_id_obj})
            # Xóa cả ảnh vừa copy
            shutil.rmtree(dest_folder)
        else:
            count_success += 1

    print("\n" + "="*50)
    print(f"✅ HOÀN TẤT! Đã thêm thành công: {count_success} người dùng.")
    print(f"📁 Ảnh avatar đã được copy vào: {BACKEND_UPLOAD_DIR}")
    print("👉 Bây giờ bạn hãy chạy lại 'python server.py' để hệ thống nạp dữ liệu mới.")

if __name__ == "__main__":
    # Đảm bảo thư mục uploads tồn tại
    os.makedirs(BACKEND_UPLOAD_DIR, exist_ok=True)
    seed_database()