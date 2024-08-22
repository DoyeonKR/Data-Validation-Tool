import tkinter as tk
from ui import create_ui

if __name__ == "__main__":
    app = tk.Tk()  # tkinter 애플리케이션 객체 생성
    create_ui(app)  # ui.py에서 정의한 UI 생성 함수 호출
    app.mainloop()  # 애플리케이션의 메인 루프 시작
