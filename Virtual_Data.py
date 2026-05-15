import firebase_admin
from firebase_admin import credentials, db
import time
import random

# --- CẤU HÌNH FIREBASE (Giống file Testfiresebase.py của bạn) ---
KEY_PATH = r"D:\DATN\IoT\serviceAccountKey.json"
DB_URL = 'https://plc1212-python-firebase-default-rtdb.asia-southeast1.firebasedatabase.app/'

if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})

firebase_ref = db.reference('Production_Monitoring')
history_ref = db.reference('Production_History')

print("🚀 Đang bắt đầu giả lập dữ liệu ảo... Nhấn Ctrl+C để dừng.")

# Khởi tạo giá trị ban đầu
total = 0
ok = 0
ng = 0

try:
    while True:
        # Giả lập sản xuất: Mỗi 3 giây tạo ra 1-3 sản phẩm mới
        new_products = random.randint(1, 3)
        total += new_products
        
        # Giả lập tỷ lệ lỗi: 90% OK, 10% NG
        for _ in range(new_products):
            if random.random() > 0.1:
                ok += 1
            else:
                ng += 1
        
        # Tính hiệu suất
        eff = round((ok / total * 100), 2) if total > 0 else 0
        evaluation = "Hệ thống tốt" if eff >= 95 else "Cần kiểm tra"
        
        # Cấu trúc Payload giống hệt dữ liệu từ PLC thực tế
        current_payload = {
            "Counters": {
                "Total_Product": total,
                "OK_Product": ok,
                "NG_Product": ng
            },
            "Analytics": {
                "Efficiency": eff,
                "Evaluation": evaluation
            },
            "System_Status": {
                "PLC_Status": "ONLINE (VIRTUAL)",
                "HSout0_OK": random.choice([True, False]),
                "HSout1_NG": (random.random() < 0.1), # 10% cơ hội báo đèn đỏ
                "Last_Update": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }

        # 1. Cập nhật dữ liệu thời gian thực
        firebase_ref.update(current_payload)
        
        # 2. Đẩy vào lịch sử để vẽ biểu đồ
        history_data = {
            "time": time.strftime("%H:%M:%S"),
            "ok": ok,
            "ng": ng,
            "eff": eff
        }
        history_ref.push(history_data)

        print(f"✅ Đã gửi: Tổng {total} | OK: {ok} | NG: {ng} | Eff: {eff}%")
        
        time.sleep(3) # Cập nhật sau mỗi 3 giây

except KeyboardInterrupt:
    print("\n🛑 Đã dừng giả lập.")