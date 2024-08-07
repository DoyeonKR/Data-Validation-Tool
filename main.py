import logging
from read_data import read_data
from compare_data import compare_data
from save_to_excel import save_to_excel
from ui import create_ui

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    create_ui()
