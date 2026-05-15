import tkinter as tk
import snap7
from snap7.util import get_int, get_bool
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import time
# CẤU HÌNH PLC
PLC_IP = '192.168.0.1'
RACK = 0
SLOT = 1
DB_NUMBER = 5
# CLASS GIÁM SÁT PLC
class PLCMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("HỆ THỐNG GIÁM SÁT SẢN XUẤT")
        self.root.geometry("450x650")
        self.root.resizable(False, False)
        # Tạo PLC client
        self.plc = snap7.client.Client()
        # Tạo giao diện
        self.setup_ui()
        # Kết nối PLC
        self.connect_plc()
        # Update dữ liệu liên tục
        self.update_data()
    # GIAO DIỆN
    def setup_ui(self):

        tk.Label(
            self.root,
            text="HỆ THỐNG GIÁM SÁT SẢN XUẤT",
            font=("Arial", 16, "bold")
        ).pack(pady=15)
        # ĐÈN BÁO
        led_frame = tk.Frame(self.root)
        led_frame.pack(pady=10)

        # ---------- OK ----------
        self.canvas_ok = tk.Canvas(led_frame, width=60, height=60)
        self.canvas_ok.grid(row=0, column=0, padx=25)

        self.led_ok = self.canvas_ok.create_oval(
            10, 10, 50, 50,
            fill="gray"
        )

        tk.Label(
            led_frame,
            text="HSout1 (OK)",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=0)

        # ---------- NG ----------
        self.canvas_ng = tk.Canvas(led_frame, width=60, height=60)
        self.canvas_ng.grid(row=0, column=1, padx=25)

        self.led_ng = self.canvas_ng.create_oval(
            10, 10, 50, 50,
            fill="gray"
        )

        tk.Label(
            led_frame,
            text="HSout0 (NG)",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=1)
        # HIỂN THỊ DỮ LIỆU
        self.lbl_total = tk.Label(
            self.root,
            text="Tổng sản phẩm: 0",
            font=("Arial", 13)
        )
        self.lbl_total.pack(pady=10)

        self.lbl_ok = tk.Label(
            self.root,
            text="Số lượng OK: 0",
            fg="green",
            font=("Arial", 13, "bold")
        )
        self.lbl_ok.pack(pady=5)

        self.lbl_ng = tk.Label(
            self.root,
            text="Số lượng NG: 0",
            fg="red",
            font=("Arial", 13, "bold")
        )
        self.lbl_ng.pack(pady=5)
        # HIỆU SUẤT
        tk.Frame(
            self.root,
            height=2,
            bd=1,
            relief="sunken"
        ).pack(fill="x", padx=25, pady=20)

        self.lbl_eff = tk.Label(
            self.root,
            text="Hiệu suất: 0%",
            font=("Arial", 15, "bold")
        )
        self.lbl_eff.pack(pady=10)

        self.lbl_eval = tk.Label(
            self.root,
            text="Đánh giá: Đang chờ dữ liệu...",
            font=("Arial", 12, "italic")
        )
        self.lbl_eval.pack(pady=5)
        # TRẠNG THÁI PLC
        self.lbl_status = tk.Label(
            self.root,
            text="PLC: Chưa kết nối",
            fg="red",
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
                        text=f"Đã kết nối PLC: {PLC_IP}",
                        fg="green"
                    )

                    print("KẾT NỐI PLC THÀNH CÔNG")

                else:

                    self.lbl_status.config(
                        text="Không thể kết nối PLC",
                        fg="red"
                    )

        except Exception as e:

            print("LỖI KẾT NỐI:", e)

            self.lbl_status.config(
                text="Lỗi kết nối PLC",
                fg="red"
            )
    # ĐỌC DỮ LIỆU PLC
    def update_data(self):

        try:

            # Nếu mất kết nối -> kết nối lại
            if not self.plc.get_connected():
                self.connect_plc()

            # ĐỌC DB5
            data = self.plc.db_read(DB_NUMBER, 0, 7)
            # ĐỌC INT
            total_product = get_int(data, 0)
            ok_product = get_int(data, 2)
            ng_product = get_int(data, 4)
            # ĐỌC BOOL
            hsout0_ng = get_bool(data, 6, 0)
            hsout1_ok = get_bool(data, 6, 1)
            # UPDATE ĐÈN
            if hsout1_ok:
                self.canvas_ok.itemconfig(
                    self.led_ok,
                    fill="lime"
                )
            else:
                self.canvas_ok.itemconfig(
                    self.led_ok,
                    fill="gray"
                )

            if hsout0_ng:
                self.canvas_ng.itemconfig(
                    self.led_ng,
                    fill="red"
                )
            else:
                self.canvas_ng.itemconfig(
                    self.led_ng,
                    fill="gray"
                )

            # UPDATE LABEL
            self.lbl_total.config(
                text=f"Tổng sản phẩm: {total_product}"
            )

            self.lbl_ok.config(
                text=f"Số lượng OK: {ok_product}"
            )

            self.lbl_ng.config(
                text=f"Số lượng NG: {ng_product}"
            )
            # TÍNH HIỆU SUẤT
            if total_product > 0:

                efficiency = (ok_product / total_product) * 100

                self.lbl_eff.config(
                    text=f"Hiệu suất: {efficiency:.2f}%"
                )

                if efficiency >= 95:

                    self.lbl_eval.config(
                        text="Đánh giá: Hệ thống hoạt động tốt",
                        fg="green"
                    )

                else:

                    self.lbl_eval.config(
                        text="Đánh giá: Cần kiểm tra lại",
                        fg="red"
                    )

            else:

                self.lbl_eff.config(
                    text="Hiệu suất: 0%"
                )

                self.lbl_eval.config(
                    text="Đánh giá: Chưa có dữ liệu",
                    fg="gray"
                )

        except Exception as e:

            print("LỖI ĐỌC PLC:", e)

            self.lbl_status.config(
                text="Mất kết nối PLC",
                fg="red"
            )
        # LẶP UPDATE
        self.root.after(200, self.update_data)
# MAIN
if __name__ == "__main__":

    root = tk.Tk()

    app = PLCMonitor(root)

    root.mainloop()