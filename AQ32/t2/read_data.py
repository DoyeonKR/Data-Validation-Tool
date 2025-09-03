import io
import pandas as pd
from AQ32.t2.mapping_dict_t2 import mapping_dict

def _read_csv_robust(path: str) -> pd.DataFrame:
    for enc in ("utf-8-sig", "cp949", "euc-kr", "iso-8859-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8", errors="ignore")
    return pd.read_csv(io.StringIO(text))

def read_data(csv_path: str, excel_path: str):
    csv_df = _read_csv_robust(csv_path)
    answer_df = pd.read_excel(excel_path)

    csv_df.columns = csv_df.columns.str.strip()
    answer_df.columns = answer_df.columns.str.strip()

    # Patient ID 추출
    if "session_id" in answer_df.columns:
        answer_df["Patient ID"] = answer_df["session_id"].astype(str).str.extract(r"(adni_\d+s\d{4}|sub_\d+)")
    else:
        answer_df["Patient ID"] = pd.NA

    # display_name 매핑
    if {"ROI", "roi_index"} <= set(answer_df.columns):
        answer_df["display_name"] = answer_df.apply(
            lambda row: mapping_dict.get((row["ROI"], row["roi_index"]), None), axis=1
        )
    else:
        answer_df["display_name"] = None

    # CSV Patient ID 보정
    if "Patient ID" not in csv_df.columns:
        if "session_id" in csv_df.columns:
            csv_df["Patient ID"] = csv_df["session_id"].astype(str).str.extract(r"(sub_\d+)")
        else:
            raise ValueError("CSV 파일에 'Patient ID' 또는 'session_id' 컬럼이 없습니다.")

    return csv_df, answer_df
