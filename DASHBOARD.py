import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import time
import io

# =========================================================
# 1. CẤU HÌNH FIREBASE
# =========================================================
KEY_PATH = r"D:\DATN\IoT\serviceAccountKey.json"
DB_URL = "https://plc1212-python-firebase-default-rtdb.asia-southeast1.firebasedatabase.app/"

if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})

# =========================================================
# 2. CẤU HÌNH TRANG & CSS (Giao diện tối chuyên nghiệp)
# =========================================================
st.set_page_config(page_title="PLC IoT Dashboard", layout="wide")

# Tự động làm mới trang mỗi 2 giây (thay thế cho while True)
st_autorefresh(interval=2000, key="data_refresh")

st.markdown("""
    <style>
    .kpi-box { color: white; padding: 10px; }
    .kpi-label { font-size: 14px; font-weight: bold; color: #f0f2f6; text-transform: uppercase; }
    .kpi-value { font-size: 50px; font-weight: bold; color: white; }
    .status-bar { 
        background-color: #112a1d; 
        color: #4ade80; 
        padding: 15px; 
        border-radius: 5px; 
        font-size: 18px; 
        margin-bottom: 25px; 
        border-left: 5px solid #22c55e;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# 3. SIDEBAR - QUẢN LÝ DỮ LIỆU
# =========================================================
with st.sidebar:
    st.header("🛠️ Quản trị hệ thống")
    if st.button("🗑️ Xoá lịch sử sản xuất"):
        db.reference("Production_History").set({})
        st.success("Đã xoá lịch sử!")
        time.sleep(1)
        st.rerun()

    if st.button("🔄 Reset bộ đếm (về 0)"):
        db.reference("Production_Monitoring/Counters").update({
            "Total_Product": 0, "OK_Product": 0, "NG_Product": 0
        })
        st.success("Đã reset bộ đếm!")
        time.sleep(1)
        st.rerun()

# =========================================================
# 4. TRUY XUẤT DỮ LIỆU TỪ FIREBASE
# =========================================================
live_ref = db.reference("Production_Monitoring")
history_ref = db.reference("Production_History")

data = live_ref.get()

if data:
    counters = data.get("Counters", {})
    total = counters.get("Total_Product", 0)
    ok = counters.get("OK_Product", 0)
    ng = counters.get("NG_Product", 0)
    
    # Tính hiệu suất
    eff = round((ok / total * 100), 1) if total > 0 else 0

    # --- HIỂN THỊ GIAO DIỆN ---
    st.markdown("<h1 style='color: white;'>SMART FACTORY IoT DASHBOARD</h1>", unsafe_allow_html=True)

    # HÀNG 1: KPI (Thiết kế giống ảnh mẫu)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-label">TOTAL PRODUCT</div><div class="kpi-value">{total}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-label">OK PRODUCT</div><div class="kpi-value">{ok}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-label">NG PRODUCT</div><div class="kpi-value">{ng}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-box"><div class="kpi-label">EFFICIENCY</div><div class="kpi-value">{eff}%</div></div>', unsafe_allow_html=True)

    # THANH STATUS
    status_msg = "Cần kiểm tra" if ng > 0 else "Hoạt động tốt"
    st.markdown(f'<div class="status-bar">STATUS: {status_msg}</div>', unsafe_allow_html=True)

    # --- HÀNG 2: BIỂU ĐỒ ---
    st.divider()
    history = history_ref.order_by_key().limit_to_last(100).get()
    
    if history:
        df = pd.DataFrame(list(history.values()))
        df["time"] = pd.to_datetime(df["time"], format='mixed')
        df = df.sort_values("time")

        fig = px.area(df, x="time", y=["ok", "ng"], 
                     title="Xu hướng sản xuất (Real-time Area Chart)",
                     color_discrete_map={"ok": "#2ecc71", "ng": "#e74c3c"},
                     template="plotly_dark")
        
        # Vì không dùng while True, không cần lo lắng về Duplicate Key nữa
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Đang chờ dữ liệu lịch sử từ hệ thống...")

    # --- PHẦN BẢNG SỐ LIỆU CẬP NHẬT LIÊN TỤC ---
    # Lấy 50 bản ghi mới nhất từ lịch sử
    history = history_ref.order_by_key().limit_to_last(50).get()
    
    if history:
        # 1. Chuyển đổi dữ liệu sang DataFrame
        df = pd.DataFrame(list(history.values()))
        
        # 2. Xử lý thời gian (với format mixed để tránh lỗi format như trước)
        df["time"] = pd.to_datetime(df["time"], format='mixed')
        
        # 3. Sắp xếp mới nhất lên đầu
        df = df.sort_values(by="time", ascending=False)
        
        df.insert(0, 'STT', range(1, len(df) + 1))
        # 4. Đổi tên cột một cách AN TOÀN (chỉ đổi những cột chắc chắn có)
        # Cách này giúp tránh lỗi "Length mismatch" nếu database thừa/thiếu cột
        rename_dict = {
            "STT": "STT",
            "time": "Thời gian",
            "total": "Tổng số",
            "ok": "Đạt (OK)",
            "ng": "Lỗi (NG)",
            "efficiency": "Hiệu suất (%)"
        }
        df = df.rename(columns=rename_dict)
        
        # Danh sách các cột muốn hiển thị theo thứ tự
        display_cols = ["STT", "Thời gian", "Tổng số", "Đạt (OK)", "Lỗi (NG)", "Hiệu suất (%)"]
        
        # Lọc lại những cột thực sự tồn tại để tránh lỗi nếu database thiếu cột
        available_cols = [c for c in display_cols if c in df.columns]

        st.subheader("📋 Nhật ký sản xuất chi tiết")
        
        # HIỂN THỊ BẢNG
        st.dataframe(
            df[available_cols], 
            use_container_width=True, 
            height=400,
            hide_index=True # <--- DÒNG NÀY GIÚP BỎ CỘT NGOÀI CÙNG BÊN TRÁI
        )

        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df[available_cols].to_excel(writer, index=False, sheet_name='Sheet1')

        buffer.seek(0)
        st.download_button(
            label="📥 Tải dữ liệu báo cáo (.xlsx)",
            data=buffer,
            file_name=f"production_report_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("Chưa có dữ liệu lịch sử.")

else:
    st.warning("⚠️ Không tìm thấy dữ liệu trên Firebase. Vui lòng kiểm tra kết nối PLC.")