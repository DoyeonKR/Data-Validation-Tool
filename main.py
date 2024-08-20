import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import importlib

# 전역 변수
result_file_path = ""
target_file_path = ""
output_file_path = ""
result_label = None
target_label = None
output_label = None
progress_bar = None


# 동적으로 모듈을 불러오는 함수
def load_module(module_name, func_name):
    module = importlib.import_module(module_name)
    return getattr(module, func_name)


# 각 버튼의 기능 구현
def select_result_file():
    global result_file_path
    result_file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if result_file_path and result_label:
        result_label.config(text=f"Result File: {os.path.basename(result_file_path)}")


def select_target_file():
    global target_file_path
    target_file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if target_file_path and target_label:
        target_label.config(text=f"Target File: {os.path.basename(target_file_path)}")


def select_output_directory():
    global output_file_path
    output_file_path = filedialog.askdirectory()
    if output_file_path and output_label:
        output_label.config(text=f"Output Directory: {output_file_path}")


def run(read_data, compare_data, save_to_excel, frame_name):
    if not result_file_path or not target_file_path or not output_file_path:
        messagebox.showerror("Error", "Please select all files (result, target, and output directory)")
        return

    if progress_bar:
        progress_bar.grid(row=11, column=0, pady=10, columnspan=2)
        progress_bar.start()

    def task():
        try:
            csv_df, excel_df_filtered = read_data(target_file_path, result_file_path)
            results_df, rois = compare_data(csv_df, excel_df_filtered)
            output_file = os.path.join(output_file_path, f'{frame_name}_Results.xlsx')
            save_to_excel(results_df, output_file, rois)
            if progress_bar:
                progress_bar.stop()
                progress_bar.grid_remove()
            messagebox.showinfo("Success",
                                f"Results have been saved to {output_file}\n\nNew 'Difference' column added for each ROI.")
        except Exception as e:
            if progress_bar:
                progress_bar.stop()
                progress_bar.grid_remove()
            messagebox.showerror("Error", str(e))

    threading.Thread(target=task).start()



# UI 구성
def show_frame(frame):
    frame.tkraise()


def create_ui():
    global result_label, target_label, output_label, progress_bar

    root = tk.Tk()
    root.title("Main UI")
    root.geometry("1200x700")

    # Grid 설정
    root.grid_rowconfigure(1, weight=0)
    root.grid_rowconfigure(2, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # 상단 버튼 메뉴바 생성
    top_frame = ttk.Frame(root)
    top_frame.grid(row=0, column=0, sticky="ew")

    # 버튼들 생성
    t1_button = ttk.Button(top_frame, text="T1", command=lambda: setup_t1_frame(t1_frame))
    t1_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    t2_button = ttk.Button(top_frame, text="T2", command=lambda: setup_t2_frame(t2_frame))
    t2_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    # 구분선 추가 (고정)
    separator = ttk.Separator(root, orient='horizontal')
    separator.grid(row=1, column=0, sticky="ew")

    # 각 페이지에 해당하는 Frame 생성
    t1_frame = ttk.Frame(root)
    t2_frame = ttk.Frame(root)

    for frame in (t1_frame, t2_frame):
        frame.grid(row=2, column=0, sticky='nsew')

    def setup_t1_frame(frame):
        global result_label, target_label, output_label, progress_bar

        show_frame(frame)
        for widget in frame.winfo_children():
            widget.destroy()

        ttk.Label(frame, text="T1 Page", font=("Helvetica", 16)).grid(row=0, column=0, pady=10, sticky='n')

        # T1 모듈에서 함수 로드
        read_data = load_module("T1.read_data", "read_data")
        compare_data = load_module("T1.compare_data", "compare_data")
        save_to_excel = load_module("T1.save_to_excel", "save_to_excel")

        ttk.Button(frame, text="Select the Result File\n(정답지 Excel)", command=select_result_file,
                   width=30).grid(row=1, column=0, pady=5)

        result_label = ttk.Label(frame, text="No file selected")
        result_label.grid(row=2, column=0, pady=10)

        ttk.Button(frame, text="Select the Analysis File\n(분석된 CSV)", command=select_target_file,
                   width=30).grid(row=3, column=0, pady=5)

        target_label = ttk.Label(frame, text="No file selected")
        target_label.grid(row=4, column=0, pady=10)

        ttk.Button(frame, text="Select the Output Directory", command=select_output_directory,
                   width=30).grid(row=5, column=0, pady=5)

        output_label = ttk.Label(frame, text="No directory selected")
        output_label.grid(row=6, column=0, pady=10)

        ttk.Button(frame, text="Run", command=lambda: run(read_data, compare_data, save_to_excel, "T1"), width=30).grid(
            row=7, column=0, pady=10)

        progress_bar = ttk.Progressbar(frame, mode='indeterminate')

    def setup_t2_frame(frame):
        global result_label, target_label, output_label, progress_bar

        show_frame(frame)
        for widget in frame.winfo_children():
            widget.destroy()

        ttk.Label(frame, text="T2 Page", font=("Helvetica", 16)).grid(row=0, column=0, pady=10, sticky='n')

        # T2 모듈에서 함수 로드
        read_data = load_module("T2.read_data", "read_data")
        compare_data = load_module("T2.compare_data", "compare_data")
        save_to_excel = load_module("T2.save_to_excel", "save_to_excel")

        ttk.Button(frame, text="Select the Result File\n(정답지 Excel)", command=select_result_file,
                   width=30).grid(row=1, column=0, pady=5)

        result_label = ttk.Label(frame, text="No file selected")
        result_label.grid(row=2, column=0, pady=10)

        ttk.Button(frame, text="Select the Analysis File\n(분석된 CSV)", command=select_target_file,
                   width=30).grid(row=3, column=0, pady=5)

        target_label = ttk.Label(frame, text="No file selected")
        target_label.grid(row=4, column=0, pady=10)

        ttk.Button(frame, text="Select the Output Directory", command=select_output_directory,
                   width=30).grid(row=5, column=0, pady=5)

        output_label = ttk.Label(frame, text="No directory selected")
        output_label.grid(row=6, column=0, pady=10)

        ttk.Button(frame, text="Run", command=lambda: run(read_data, compare_data, save_to_excel, "T2"), width=30).grid(
            row=7, column=0, pady=10)

        progress_bar = ttk.Progressbar(frame, mode='indeterminate')

    # 기본적으로 첫 페이지(T1)를 보여줌
    setup_t1_frame(t1_frame)

    root.mainloop()


if __name__ == "__main__":
    create_ui()
