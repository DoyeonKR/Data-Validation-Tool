import os
from tkinter import Tk, Frame, filedialog, messagebox, PanedWindow
from tkinter import ttk
import threading

from read_data import read_data
from compare_data import compare_data
from save_to_excel import save_to_excel

result_file_path = ""
target_file_path = ""
output_file_path = ""

def select_result_file():
    global result_file_path
    result_file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if result_file_path:
        result_label.config(text=f"Result File: {os.path.basename(result_file_path)}")

def select_target_file():
    global target_file_path
    target_file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if target_file_path:
        target_label.config(text=f"Target File: {os.path.basename(target_file_path)}")

def select_output_directory():
    global output_file_path
    output_file_path = filedialog.askdirectory()
    if output_file_path:
        output_label.config(text=f"Output Directory: {output_file_path}")

def run(read_data, compare_data, save_to_excel):
    if not result_file_path or not target_file_path or not output_file_path:
        messagebox.showerror("Error", "Please select all files (result, target, and output directory)")
        return

    progress_bar.grid(row=11, column=0, pady=10, columnspan=2)
    progress_bar.start()

    def task():
        # try:
        #     csv_df, excel_df_filtered = read_data(target_file_path, result_file_path)
        #     results_df, rois = compare_data(csv_df, excel_df_filtered)
        #     output_file = os.path.join(output_file_path, 'Results.xlsx')
        #     save_to_excel(results_df, output_file, rois)
        #     progress_bar.stop()
        #     progress_bar.grid_remove()
        #     messagebox.showinfo("Success", f"Results have been saved to {output_file}")
        # except Exception as e:
        #     progress_bar.stop()
        #     progress_bar.grid_remove()
        #     messagebox.showerror("Error", str(e))

        try:
            csv_df, excel_df_filtered = read_data(target_file_path, result_file_path)
            results_df, rois = compare_data(csv_df, excel_df_filtered)
            output_file = os.path.join(output_file_path, 'Results.xlsx')
            save_to_excel(results_df, output_file, rois)
            progress_bar.stop()
            progress_bar.grid_remove()
            messagebox.showinfo("Success", f"Results have been saved to {output_file}\n\nNew 'Difference' column added for each ROI.")
        except Exception as e:
            progress_bar.stop()
            progress_bar.grid_remove()
            messagebox.showerror("Error", str(e))

    threading.Thread(target=task).start()

def create_ui():
    global result_label, target_label, output_label, progress_bar

    root = Tk()
    root.title("Data Comparator")
    root.geometry("1200x700")  # Fixed window size

    style = ttk.Style()
    style.configure('TButton', font=('Helvetica', 12), padding=10)
    style.configure('TLabel', font=('Helvetica', 12), padding=10)
    style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'))

    paned_window = PanedWindow(root, orient='horizontal')
    paned_window.pack(fill='both', expand=True)

    button_frame = Frame(paned_window, padx=10, pady=10, bg='#2e2e2e')
    button_frame.pack_propagate(False)
    button_frame.config(width=200)
    paned_window.add(button_frame)

    main_frame = Frame(paned_window, padx=20, pady=20)
    paned_window.add(main_frame)

    # 탭 버튼 추가
    ttk.Style().configure("TButton", padding=6, relief="flat", background="#2e2e2e", foreground="black")
    tabs = ["T1", "T2-FLAIR", "MR-PET"]
    for tab in tabs:
        btn = ttk.Button(button_frame, text=tab, command=lambda t=tab: switch_tab(t, main_frame))
        btn.pack(fill='x', pady=5)

    switch_tab("T1", main_frame)

    root.mainloop()

def switch_tab(tab_name, main_frame):
    for widget in main_frame.winfo_children():
        widget.destroy()

    global result_label, target_label, output_label, progress_bar

    ttk.Label(main_frame, text=f"Tab: {tab_name}", style='Header.TLabel').grid(row=0, column=0, pady=5, columnspan=2)
    ttk.Label(main_frame, text="Select the Result File (정답지 Excel)", style='Header.TLabel').grid(row=1, column=0, pady=5, columnspan=2)
    result_label = ttk.Label(main_frame, text="No file selected")
    result_label.grid(row=2, column=0, pady=5, columnspan=2)
    ttk.Button(main_frame, text="Browse", command=select_result_file).grid(row=3, column=0, pady=5, columnspan=2)

    ttk.Label(main_frame, text="Select the Analysis File (분석된 CSV)", style='Header.TLabel').grid(row=4, column=0, pady=5, columnspan=2)
    target_label = ttk.Label(main_frame, text="No file selected")
    target_label.grid(row=5, column=0, pady=5, columnspan=2)
    ttk.Button(main_frame, text="Browse", command=select_target_file).grid(row=6, column=0, pady=5, columnspan=2)

    ttk.Label(main_frame, text="Select the Output Directory", style='Header.TLabel').grid(row=7, column=0, pady=5, columnspan=2)
    output_label = ttk.Label(main_frame, text="No directory selected")
    output_label.grid(row=8, column=0, pady=5, columnspan=2)
    ttk.Button(main_frame, text="Browse", command=select_output_directory).grid(row=9, column=0, pady=5, columnspan=2)

    ttk.Button(main_frame, text="Run", command=lambda: run(read_data, compare_data, save_to_excel)).grid(row=10, column=0, pady=10, columnspan=2)

    progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
    ttk.Label(main_frame, text="Made by SV team v1.0", anchor='s').grid(row=11, column=0, pady=5, columnspan=2)

if __name__ == "__main__":
    create_ui()
