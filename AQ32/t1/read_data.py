import io
import pandas as pd
from AQ32.t1.mapping_dict import mapping_dict


def _read_csv_robust(path: str) -> pd.DataFrame:
    """CSV 인코딩 폴백 로더 (utf-8-sig → cp949 → euc-kr → iso-8859-1 → ignore)"""
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
    """
    입력 파일 경로에서 DataFrame 로드 + 전처리.
    원본 스크립트의 1~5단계 로직을 유지합니다.
    반환: (csv_df, answer_df)
    """
    csv_df = _read_csv_robust(csv_path)
    answer_df = pd.read_excel(excel_path)

    # 3) 정답지에서 Patient ID 추출
    #  - session_id에서 (adni_숫자s숫자4자리 | sub_숫자) 패턴 추출
    if "session_id" in answer_df.columns:
        answer_df["Patient ID"] = answer_df["session_id"].astype(str).str.extract(r"(adni_\d+s\d{4}|sub_\d+)")
    else:
        answer_df["Patient ID"] = pd.NA  # 안전하게 컬럼만 생성

    # 4) 매핑 딕셔너리를 이용해 display_name 매핑
    #  - (ROI, roi_index) 튜플 키로 조회
    if {"ROI", "roi_index"} <= set(answer_df.columns):
        answer_df["display_name"] = answer_df.apply(
            lambda row: mapping_dict.get((row["ROI"], row["roi_index"]), None), axis=1
        )
    else:
        # 필요한 컬럼이 없으면 그대로 None 채움
        answer_df["display_name"] = None

    # 5) CSV에서 Patient ID 자동 추출
    if "Patient ID" not in csv_df.columns:
        if "session_id" in csv_df.columns:
            csv_df["Patient ID"] = csv_df["session_id"].astype(str).str.extract(r"(sub_\d+)")
        else:
            raise ValueError("CSV 파일에 'Patient ID' 또는 'session_id' 컬럼이 없습니다.")

    return csv_df, answer_df
