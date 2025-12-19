import os
import sys
import numpy as np
from tqdm import tqdm
from core_ai import FaceSystem

# ==============================================================================
# CẤU HÌNH ĐƯỜNG DẪN
# ==============================================================================

# 1. Thư mục chứa dữ liệu gốc dùng để HỌC (Enrollment)
FILTERED_DIR = r"D:\1.Study\1.Caohoc\K37\1.ML\1.CODE\BTCK\VGGFace2\VGGFace2_Filtered"

# 2. Thư mục chứa bộ dữ liệu TEST CỐ ĐỊNH
TEST_ROOT_DIR = r"D:\1.Study\1.Caohoc\K37\1.ML\1.CODE\BTCK\VGGFace2\TEST" 

TEST_REGISTERED_DIR = os.path.join(TEST_ROOT_DIR, "Registered")
TEST_UNKNOWN_DIR    = os.path.join(TEST_ROOT_DIR, "Unknown")

# 3. Các tham số đánh giá
THRESHOLD = 0.55

# --- CẤU HÌNH MỚI: TIÊU CHÍ ĐÚNG NGƯỜI ---
# Nếu số ảnh đúng / tổng số ảnh test >= tỷ lệ này thì coi là ĐÚNG NGƯỜI.
# Ví dụ: 3 ảnh đúng 2 => 2/3 = 0.66
PASS_RATIO = 2/3 

def evaluate():
    system = FaceSystem()
    
    # =========================================================
    # BƯỚC 1: ĐĂNG KÝ LẠI (ENROLLMENT)
    # =========================================================
    # (Để đảm bảo tính đồng bộ, nên mở lại đoạn này khi chạy thật)
    print("\n[BƯỚC 1] Đang làm sạch DB và Đăng ký dữ liệu mẫu...")
    system.users_col.delete_many({})
    system.vectors_col.delete_many({})
    
    if not os.path.exists(FILTERED_DIR):
        print("❌ Lỗi: Không tìm thấy thư mục dữ liệu lọc!")
        return

    enrolled_users = os.listdir(FILTERED_DIR)
    
    # Đăng ký lại toàn bộ
    for user_name in tqdm(enrolled_users, desc="Đang đăng ký"):
        user_dir = os.path.join(FILTERED_DIR, user_name)
        img_paths = [os.path.join(user_dir, f) for f in os.listdir(user_dir)]
        if img_paths:
            system.register_user(name=user_name, age=25, img_paths=img_paths)

    system.reload_model()
    print("✅ Đăng ký hoàn tất.")

    # =========================================================
    # BƯỚC 2: KIỂM TRA NGƯỜI QUEN (GENUINE TEST)
    # =========================================================
    print("\n[BƯỚC 2] Kiểm tra nhận diện NGƯỜI QUEN...")
    
    # Thống kê theo ẢNH (Image-level)
    stats_image = {
        "total": 0, "correct": 0, "wrong_id": 0, "rejected": 0
    }

    # Thống kê theo NGƯỜI (User-level) - MỚI
    stats_user = {
        "total_users": 0,
        "passed_users": 0, # Số người được nhận diện đúng (đạt tiêu chí 2/3)
        "failed_users": 0  # Số người hệ thống bó tay
    }

    test_users = os.listdir(TEST_REGISTERED_DIR)

    for user_name in tqdm(test_users, desc="Test Người quen"):
        user_test_path = os.path.join(TEST_REGISTERED_DIR, user_name)
        if not os.path.isdir(user_test_path): continue

        test_images = [os.path.join(user_test_path, f) for f in os.listdir(user_test_path) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if len(test_images) == 0: continue

        # Biến đếm riêng cho từng người dùng này
        correct_count_this_user = 0
        
        for img_path in test_images:
            stats_image["total"] += 1
            
            result = system.recognize(img_path, threshold=THRESHOLD)
            
            if result is None:
                stats_image["rejected"] += 1
            elif result['name'] == user_name:
                stats_image["correct"] += 1
                correct_count_this_user += 1 # Đếm số ảnh đúng của user này
            else:
                stats_image["wrong_id"] += 1
        
        # --- TÍNH TOÁN CẤP NGƯỜI DÙNG (USER LEVEL) ---
        stats_user["total_users"] += 1
        
        # Tính tỷ lệ đúng của người này
        accuracy_this_user = correct_count_this_user / len(test_images)
        
        # Kiểm tra tiêu chí (Ví dụ: đúng >= 66%)
        if accuracy_this_user >= PASS_RATIO:
            stats_user["passed_users"] += 1
        else:
            stats_user["failed_users"] += 1
            # In ra để biết ai bị fail
            # tqdm.write(f"❌ User FAIL: {user_name} (Chỉ đúng {correct_count_this_user}/{len(test_images)} ảnh)")

    # =========================================================
    # BƯỚC 3: KIỂM TRA NGƯỜI LẠ (IMPOSTER TEST)
    # =========================================================
    print("\n[BƯỚC 3] Kiểm tra khả năng từ chối NGƯỜI LẠ...")
    
    stats_imposter = {
        "total": 0, "passed": 0, "blocked": 0
    }

    if os.path.exists(TEST_UNKNOWN_DIR):
        unknown_images = []
        for root, dirs, files in os.walk(TEST_UNKNOWN_DIR):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    unknown_images.append(os.path.join(root, file))
        
        for img_path in tqdm(unknown_images, desc="Test Người lạ"):
            stats_imposter["total"] += 1
            result = system.recognize(img_path, threshold=THRESHOLD)
            if result is None:
                stats_imposter["blocked"] += 1
            else:
                stats_imposter["passed"] += 1
    else:
        print(f"⚠️ Không tìm thấy thư mục người lạ: {TEST_UNKNOWN_DIR}")

    # =========================================================
    # BƯỚC 4: BÁO CÁO KẾT QUẢ
    # =========================================================
    # 1. Chỉ số cấp Ảnh
    acc_image_genuine = 0
    if stats_image["total"] > 0:
        acc_image_genuine = (stats_image["correct"] / stats_image["total"]) * 100
    
    # 2. Chỉ số cấp Người dùng (Quan trọng)
    acc_user_level = 0
    if stats_user["total_users"] > 0:
        acc_user_level = (stats_user["passed_users"] / stats_user["total_users"]) * 100

    # 3. Chỉ số Người lạ
    far = 0 
    if stats_imposter["total"] > 0:
        far = (stats_imposter["passed"] / stats_imposter["total"]) * 100

    print("\n" + "="*60)
    print(f"📊 BÁO CÁO CHI TIẾT (Threshold = {THRESHOLD})")
    print("="*60)
    
    print("\n🎯 1. ĐỘ CHÍNH XÁC THEO NGƯỜI (User Accuracy) - QUAN TRỌNG NHẤT:")
    print(f"   (Tiêu chí: Đúng >= {PASS_RATIO*100:.0f}% số ảnh test)")
    print(f"   - Tổng số người test:  {stats_user['total_users']} người")
    print(f"   - ✅ Nhận đúng người:  {stats_user['passed_users']} người")
    print(f"   - ❌ Nhận sai người:   {stats_user['failed_users']} người")
    print(f"   👉 TỶ LỆ THÀNH CÔNG:   {acc_user_level:.2f}%")

    print("\n📷 2. CHI TIẾT TỪNG ẢNH (Image Accuracy):")
    print(f"   - Tổng số ảnh test:    {stats_image['total']}")
    print(f"   - ✅ Ảnh đúng:         {stats_image['correct']} ({acc_image_genuine:.2f}%)")
    print(f"   - ❌ Ảnh sai tên:      {stats_image['wrong_id']}")
    print(f"   - ⚠️ Ảnh bị từ chối:   {stats_image['rejected']}")
    
    print("\n🛡️ 3. ĐỐI VỚI NGƯỜI LẠ (Security):")
    print(f"   - Tổng số ảnh test:    {stats_imposter['total']}")
    print(f"   - 🛡️ Chặn thành công:  {stats_imposter['blocked']}")
    print(f"   - 🚨 Bị lọt lưới (FAR):{stats_imposter['passed']} ({far:.2f}%)")
    
    print("-" * 60)
    if acc_user_level > 95:
        print("🏆 HỆ THỐNG RẤT XUẤT SẮC! Đạt tiêu chuẩn thương mại.")
    elif acc_user_level > 85:
        print("✅ HỆ THỐNG TỐT. Có thể dùng ổn định.")
    else:
        print("⚠️ CẦN CẢI THIỆN. Kiểm tra lại dữ liệu đầu vào.")

if __name__ == "__main__":
    evaluate()