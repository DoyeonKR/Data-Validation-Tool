import pandas as pd

def _validate_row(row: pd.Series, csv_data: pd.DataFrame):
    """
    원본 validate_row(row, csv_data) 로직 그대로 유지.
    - 값 비교 시 min/max 뒤바뀜 방지 (lower/upper로 재정의)
    - 결과 레이블: PASS / FAIL / No Match / Invalid
    """
    patient_id = row.get("Patient ID")
    column = row.get("display_name")
    min_val = row.get("Engine_raw_vol_min")
    max_val = row.get("Engine_raw_vol_max")

    actual_value = None

    if pd.isna(patient_id) or not isinstance(patient_id, str):
        return None, "No Match"

    if pd.isna(column) or column not in csv_data.columns:
        return None, "No Match"

    # 부분 일치(contains)로 환자 로우 매칭 (원본 유지)
    patient_data = csv_data[csv_data["Patient ID"].astype(str).str.contains(patient_id, na=False)]
    if patient_data.empty:
        return None, "No Match"

    try:
        value = float(patient_data.iloc[0][column])
        actual_value = value

        if pd.isna(value):
            return value, "Invalid"

        # 항상 작은 쪽이 min, 큰 쪽이 max 되도록
        lower = min(min_val, max_val)
        upper = max(min_val, max_val)

        if lower <= value <= upper:
            return value, "PASS"
        else:
            return value, "FAIL"

    except Exception:
        return None, "Invalid"


def compare_data(csv_df: pd.DataFrame, answer_df: pd.DataFrame):
    """
    원본 스크립트의 6~8단계 로직을 함수로 재현.
    - 각 로우 validate 후 Engine_raw_vol_actual / Result 컬럼 생성
    - '엑셀에는 있는데 CSV에 아예 없는 session_id' 처리 등은
      원본 스크립트가 T1 볼류메트리 기준에서 정의하지 않았으므로 그대로 생략.
    반환: (results_df, rois)
    """
    # 진행률/시간 로깅(TQDM/print)은 서버용에서는 제거 (원본 계산 로직만 유지)
    actuals = []
    results = []

    # answer_df 각 행 비교
    for _, row in answer_df.iterrows():
        value, result = _validate_row(row, csv_df)
        actuals.append(value)
        results.append(result)

    out_df = answer_df.copy()
    out_df["Engine_raw_vol_actual"] = actuals
    out_df["Result"] = results

    # rois: display_name 유니크 리스트(공통 시그니처 호환용)
    rois = sorted(out_df["display_name"].dropna().unique().tolist()) if "display_name" in out_df.columns else []

    return out_df, rois
