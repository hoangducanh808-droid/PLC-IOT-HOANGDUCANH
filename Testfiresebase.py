
import tkinter as tk
import snap7
from snap7.util import get_int, get_bool
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import time
import os
# CẤU HÌNH PLC
PLC_IP = '192.168.0.1'
RACK = 0
SLOT = 1
DB_NUMBER = 5
# CẤU HÌNH FIREBASE
KEY_PATH = r"D:\DATN\IoT\serviceAccountKey.json"
DB_URL = 'https://plc1212-python-firebase-default-rtdb.asia-southeast1.firebasedatabase.app/'
firebase_ref = None
# KHỞI TẠO FIREBASE
try:
    if not firebase_admin._apps:
        if os.path.exists(KEY_PATH):
            cred = credentials.Certificate(KEY_PATH)

            firebase_admin.initialize_app(
                cred,
                {
                    'databaseURL': DB_URL
                }
            )
            print("=== FIREBASE CONNECTED ===")
        else:
            print("KHÔNG TÌM THẤY FILE JSON")
    firebase_ref = db.reference('Production_Monitoring')
except Exception as e:
    print("LỖI FIREBASE:", e)
# CLASS GIÁM SÁT PLC
class PLCMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title(
            "HỆ THỐNG GIÁM SÁT SẢN XUẤT - HOÀNG ĐỨC ANH - 101200212"
        )
        self.root.geometry("450x650")
        self.root.resizable(False, False)
        self.last_sent_data = None
        # PLC CLIENT
        self.plc = snap7.client.Client()
        # UI
        self.setup_ui()
        # CONNECT PLC
        self.connect_plc()
        # UPDATE LOOP
        self.update_data()
    # GIAO DIỆN
    def setup_ui(self):
        tk.Label(
            self.root,
            text="HỆ THỐNG GIÁM SÁT SẢN XUẤT",
            font=("Arial", 16, "bold"),
            fg="#1a237e"
        ).pack(pady=15)
        # LED FRAME
        led_frame = tk.Frame(self.root)
        led_frame.pack(pady=10)
        # LED OK
        self.canvas_ok = tk.Canvas(
            led_frame,
            width=60,
            height=60
        )
        self.canvas_ok.grid(
            row=0,
            column=0,
            padx=25
        )
        self.led_ok = self.canvas_ok.create_oval(
            10,
            10,
            50,
            50,
            fill="gray"
        )
        tk.Label(
            led_frame,
            text="OK (HSout0)",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=0)
        # LED NG
        self.canvas_ng = tk.Canvas(
            led_frame,
            width=60,
            height=60
        )
        self.canvas_ng.grid(
            row=0,
            column=1,
            padx=25
        )
        self.led_ng = self.canvas_ng.create_oval(
            10,
            10,
            50,
            50,
            fill="gray"
        )
        tk.Label(
            led_frame,
            text="NG (HSout1)",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=1)
        # DATA LABELS
        self.lbl_total = tk.Label(
            self.root,
            text="Tổng sản phẩm: 0",
            font=("Arial", 13)
        )
        self.lbl_total.pack(pady=10)
        self.lbl_ok = tk.Label(
            self.root,
            text="Số lượng OK: 0",
            fg="#2e7d32",
            font=("Arial", 13, "bold")
        )
        self.lbl_ok.pack(pady=5)
        self.lbl_ng = tk.Label(
            self.root,
            text="Số lượng NG: 0",
            fg="#c62828",
            font=("Arial", 13, "bold")
        )
        self.lbl_ng.pack(pady=5)
        # SEPARATOR
        tk.Frame(
            self.root,
            height=2,
            bd=1,
            relief="sunken"
        ).pack(fill="x", padx=25, pady=20)
        # EFFICIENCY
        self.lbl_eff = tk.Label(
            self.root,
            text="Hiệu suất: 0%",
            font=("Arial", 18, "bold"),
            fg="#0d47a1"
        )
        self.lbl_eff.pack(pady=10)
        self.lbl_eval = tk.Label(
            self.root,
            text="Đánh giá: Chờ dữ liệu...",
            font=("Arial", 12, "italic")
        )
        self.lbl_eval.pack(pady=5)
        # STATUS
        self.lbl_status = tk.Label(
            self.root,
            text="PLC: Đang kết nối...",
            fg="orange",
            font=("Arial", 10, "bold")
        )
        self.lbl_status.pack(side="bottom", pady=15)
    # KẾT NỐI PLC
    def connect_plc(self):
        try:
            if not self.plc.get_connected():
                self.plc.connect(
                    PLC_IP,
                    RACK,
                    SLOT
                )
                if self.plc.get_connected():
                    self.lbl_status.config(
                        text=f"PLC ONLINE : {PLC_IP}",
                        fg="green"
                    )
                    print("=== PLC CONNECTED ===")
                else:
                    self.lbl_status.config(
                        text="PLC OFFLINE",
                        fg="red"
                    )
        except Exception as e:
            print("LỖI PLC:", e)
            self.lbl_status.config(
                text="PLC ERROR",
                fg="red"
            )
    # UPDATE DATA
    def update_data(self):
        try:
            if not self.plc.get_connected():
                self.connect_plc()
            else:
                # READ DB5
                data = self.plc.db_read(
                    DB_NUMBER,
                    0,
                    7
                )
                total = get_int(data, 0)
                ok = get_int(data, 2)
                ng = get_int(data, 4)
                # HSout0 = OK
                hsout0_ok = get_bool(data, 6, 0)
                # HSout1 = NG
                hsout1_ng = get_bool(data, 6, 1)
                # CALCULATE EFFICIENCY
                eff = round(
                    (ok / total * 100),
                    2
                ) if total > 0 else 0
                # UPDATE UI
                self.lbl_total.config(
                    text=f"Tổng sản phẩm: {total}"
                )
                self.lbl_ok.config(
                    text=f"Số lượng OK: {ok}"
                )
                self.lbl_ng.config(
                    text=f"Số lượng NG: {ng}"
                )
                self.lbl_eff.config(
                    text=f"Hiệu suất: {eff}%"
                )
                # LED STATUS
                self.canvas_ok.itemconfig(
                    self.led_ok,
                    fill="#00ff00" if hsout0_ok else "gray"
                )
                self.canvas_ng.itemconfig(
                    self.led_ng,
                    fill="#ff0000" if hsout1_ng else "gray"
                )
                # EVALUATION
                if total > 0:
                    if eff >= 95:
                        evaluation = "Hệ thống hoạt động tốt"
                        eval_color = "green"
                    else:
                        evaluation = "Tỷ lệ NG cao - Kiểm tra hệ thống"
                        eval_color = "red"
                    self.lbl_eval.config(
                        text=f"Đánh giá: {evaluation}",
                        fg=eval_color
                    )
                else:
                    evaluation = "Chưa có dữ liệu"
                # FIREBASE DATA STRUCTURE
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

                        "PLC_Status": "ONLINE",

                        "HSout0_OK": hsout0_ok,

                        "HSout1_NG": hsout1_ng,

                        "Last_Update":
                            time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }

                # SEND FIREBASE
                if firebase_ref and current_payload != self.last_sent_data:
                    firebase_ref.update(
                        current_payload
                    )
                    self.last_sent_data = current_payload
                    print(
                        f"[{time.strftime('%H:%M:%S')}] "
                        f"Firebase Sync OK"
                    )
        except Exception as e:
            print("LỖI UPDATE:", e)
            self.lbl_status.config(
                text="MẤT KẾT NỐI PLC",
                fg="red"
            )

        # LOOP 1 SECOND
        self.root.after(1000, self.update_data)
# MAIN
if __name__ == "__main__":
    root = tk.Tk()
    app = PLCMonitor(root)
    root.mainloop()
