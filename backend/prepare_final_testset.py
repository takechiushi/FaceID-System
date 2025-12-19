import os
import random
import shutil
from tqdm import tqdm

# ==============================================================================
# CẤU HÌNH ĐƯỜNG DẪN (BẠN CHỈ CẦN SỬA Ở ĐÂY)
# ==============================================================================

# 1. Thư mục chứa 5 ảnh mẫu ĐÃ LỌC (Dùng để biết danh sách người quen)
ENROLLED_DIR = r"D:\1.Study\1.Caohoc\K37\1.ML\1.CODE\BTCK\VGGFace2\VGGFace2_Filtered"

# 2. Kho ảnh gốc TRAIN (Để lấy ảnh test cho người quen)
SRC_TRAIN_DIR = r"D:\1.Study\1.Caohoc\K37\1.ML\1.CODE\BTCK\VGGFace2\train"

# 3. Kho ảnh gốc VAL (Để lấy ảnh test cho người lạ)
SRC_VAL_DIR = r"D:\1.Study\1.Caohoc\K37\1.ML\1.CODE\BTCK\VGGFace2\val"

# 4. Thư mục ĐÍCH (Nơi sẽ tạo ra bộ dataset TEST hoàn chỉnh)
OUTPUT_DIR = r"D:\1.Study\1.Caohoc\K37\1.ML\1.CODE\BTCK\VGGFace2\TEST"

# 5. Cấu hình số lượng
IMAGES_PER_PERSON = 3       # Lấy 5 ảnh mỗi người
NUM_STRANGERS = 60

# ==============================================================================
# HÀM XỬ LÝ CHÍNH
# ==============================================================================

def create_unified_testset():
    # 1. Kiểm tra đầu vào
    if not os.path.exists(ENROLLED_DIR):
        print(f"❌ Lỗi: Không tìm thấy thư mục đăng ký: {ENROLLED_DIR}")
        return

    # 2. Tạo cấu trúc thư mục đầu ra
    reg_output_dir = os.path.join(OUTPUT_DIR, "Registered")
    unk_output_dir = os.path.join(OUTPUT_DIR, "Unknown")

    # Xóa cũ tạo mới cho sạch sẽ
    if os.path.exists(OUTPUT_DIR):
        print("⚠️ Đang xóa thư mục TEST cũ để tạo mới...")
        shutil.rmtree(OUTPUT_DIR)
    
    os.makedirs(reg_output_dir)
    os.makedirs(unk_output_dir)
    print(f"✅ Đã tạo cấu trúc thư mục tại: {OUTPUT_DIR}")

    # ---------------------------------------------------------
    # PHẦN 1: TẠO DỮ LIỆU "ĐÃ ĐĂNG KÝ" (REGISTERED)
    # ---------------------------------------------------------
    # Lấy danh sách ID người quen từ folder đã lọc
    registered_ids = [d for d in os.listdir(ENROLLED_DIR) if os.path.isdir(os.path.join(ENROLLED_DIR, d))]
    
    print(f"\n🚀 [PHẦN 1] Đang xử lý {len(registered_ids)} người ĐÃ ĐĂNG KÝ...")
    
    count_reg = 0
    for user_id in tqdm(registered_ids, desc="Copying Registered"):
        # Tìm folder gốc của người này trong train
        src_path = os.path.join(SRC_TRAIN_DIR, user_id)
        dst_path = os.path.join(reg_output_dir, user_id)
        
        if not os.path.exists(src_path):
            continue # Bỏ qua nếu không tìm thấy ảnh gốc
            
        # Lấy danh sách ảnh
        images = [f for f in os.listdir(src_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        
        # Chọn ngẫu nhiên 5 ảnh (Khác 5 ảnh đã lọc nếu có thể, nhưng với số lượng lớn thì random là đủ)
        random.seed(42) # Cố định random để lần sau chạy vẫn thế
        if len(images) > IMAGES_PER_PERSON:
            selected_imgs = random.sample(images, IMAGES_PER_PERSON)
        else:
            selected_imgs = images
            
        # Copy sang thư mục TEST/Registered
        os.makedirs(dst_path, exist_ok=True)
        for img in selected_imgs:
            shutil.copy2(os.path.join(src_path, img), os.path.join(dst_path, img))
        count_reg += 1

    # ---------------------------------------------------------
    # PHẦN 2: TẠO DỮ LIỆU "CHƯA ĐĂNG KÝ" (UNKNOWN)
    # ---------------------------------------------------------
    if os.path.exists(SRC_VAL_DIR):
        all_strangers = [d for d in os.listdir(SRC_VAL_DIR) if os.path.isdir(os.path.join(SRC_VAL_DIR, d))]
        
        # Chỉ lấy số lượng người lạ giới hạn (ví dụ 200 người)
        if len(all_strangers) > NUM_STRANGERS:
            random.seed(999) 
            selected_strangers = random.sample(all_strangers, NUM_STRANGERS)
        else:
            selected_strangers = all_strangers

        print(f"\n🚀 [PHẦN 2] Đang xử lý {len(selected_strangers)} người LẠ (Chưa đăng ký)...")

        count_unk = 0
        for stranger_id in tqdm(selected_strangers, desc="Copying Unknown"):
            src_path = os.path.join(SRC_VAL_DIR, stranger_id)
            dst_path = os.path.join(unk_output_dir, stranger_id)
            
            images = [f for f in os.listdir(src_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            
            if not images: continue
            
            if len(images) > IMAGES_PER_PERSON:
                random.seed(42)
                selected_imgs = random.sample(images, IMAGES_PER_PERSON)
            else:
                selected_imgs = images
            
            os.makedirs(dst_path, exist_ok=True)
            for img in selected_imgs:
                shutil.copy2(os.path.join(src_path, img), os.path.join(dst_path, img))
            count_unk += 1
    else:
        print(f"⚠️ Cảnh báo: Không tìm thấy thư mục val tại {SRC_VAL_DIR}")

    # ---------------------------------------------------------
    # KẾT THÚC
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print("✅ HOÀN TẤT QUÁ TRÌNH TẠO DỮ LIỆU TEST!")
    print(f"📂 Thư mục gốc: {OUTPUT_DIR}")
    print(f"   ├── 🟢 Registered (Đã đăng ký): {count_reg} người")
    print(f"   └── 🔴 Unknown    (Chưa đăng ký): {count_unk} người")
    print("="*50)

if __name__ == "__main__":
    create_unified_testset()