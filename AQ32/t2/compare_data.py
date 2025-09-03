import pandas as pd
from typing import Tuple

# 원본 validate_row 로직을 그대로 함수화
def _validate_row(row: pd.Series, csv_data: pd.DataFrame):
    patient_id = row.get("Patient ID")
    column = row.get("display_name")
    min_val = row.get("Engine_raw_vol_min")
    max_val = row.get("Engine_raw_vol_max")

    actual_value = None

    if pd.isna(patient_id) or not isinstance(patient_id, str):
        return None, "No Match"

    if pd.isna(column) or column not in csv_data.columns:
        return None, "No Match"

    patient_series = csv_data["Patient ID"].astype(str)
    patient_data = csv_data[patient_series.str.contains(patient_id, na=False)]
    if patient_data.empty:
        return None, "No Match"

    try:
        value = float(patient_data.iloc[0][column])
        actual_value = value

        if pd.isna(value):
            return value, "Invalid"

        lower = min(min_val, max_val)
        upper = max(min_val, max_val)

        if lower <= value <= upper:
            return value, "PASS"
        else:
            return value, "FAIL"

    except Exception:
        return None, "Invalid"

def compare_data(csv_df: pd.DataFrame, answer_df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """
    - 원본 스크립트의 비교 흐름을 그대로 수행
    - 반환: (results_df, rois)
    """
    # 진행률/시간 출력(tqdm, time)은 API 환경에선 제외하고 동일 계산만 수행
    actuals = []
    results = []
    for _, row in answer_df.iterrows():
        value, result = _validate_row(row, csv_df)
        actuals.append(value)
        results.append(result)

    answer_df = answer_df.copy()
    answer_df["Engine_raw_vol_actual"] = actuals
    answer_df["Result"] = results

    # rois: 공통 시그니처 호환용
    rois = (
        answer_df["display_name"].dropna().astype(str).unique().tolist()
        if "display_name" in answer_df.columns
        else []
    )
    return answer_df, rois
