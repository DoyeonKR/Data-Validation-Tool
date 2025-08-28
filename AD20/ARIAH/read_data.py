# AD/ARIAH/read_data.py
import io
import pandas as pd

def _read_csv_robust(path: str) -> pd.DataFrame:
    for enc in ("utf-8-sig", "cp949", "euc-kr", "iso-8859-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    # 최후 수단: 손실 허용
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8", errors="ignore")
    return pd.read_csv(io.StringIO(text))

def read_data(csv_path: str, excel_path: str):
    """
    process_comparison 단계 1:
    - 업로드된 파일 경로에서 DataFrame 로드 (원본 로직 변경 없음)
    - 반환: (csv_df, excel_df)  # excel_df_filtered가 아니라도 OK
    """
    csv_df = _read_csv_robust(csv_path)
    excel_df = pd.read_excel(excel_path)
    return csv_df, excel_df
