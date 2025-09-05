import pandas as pd  # 판다스: 표 형태(데이터프레임) 데이터 처리 라이브러리

def _validate_row(row: pd.Series, csv_data: pd.DataFrame):  # 한 행(row)과 CSV 전체 데이터로 검증하는 내부 함수 정의
    """
    원본 validate_row(row, csv_data) 로직 그대로 유지.
    - 값 비교 시 min/max 뒤바뀜 방지 (lower/upper로 재정의)
    - 결과 레이블: PASS / FAIL / No Match / Invalid
    """
    patient_id = row.get("Patient ID")  # 현재 정답 행에서 'Patient ID' 값 가져오기 (없으면 None)
    column = row.get("display_name")    # 비교할 컬럼명(표시 이름) 가져오기
    min_val = row.get("Engine_raw_vol_min")  # 허용 최소값
    max_val = row.get("Engine_raw_vol_max")  # 허용 최대값

    actual_value = None  # 실제 측정값(비교 대상)을 담아둘 변수 초기화

    if pd.isna(patient_id) or not isinstance(patient_id, str):  # 환자 ID가 없거나 문자열이 아니면
        return None, "No Match"  # 매칭 불가로 처리

    if pd.isna(column) or column not in csv_data.columns:  # 비교할 컬럼명이 없거나 CSV에 존재하지 않으면
        return None, "No Match"  # 매칭 불가로 처리

    # 부분 일치(contains)로 환자 로우 매칭 (원본 유지) — session_id 전체가 아닌 일부 포함도 허용
    patient_data = csv_data[csv_data["Patient ID"].astype(str).str.contains(patient_id, na=False)]  # 문자열 포함 필터
    if patient_data.empty:  # 해당 환자 레코드가 하나도 없다면
        return None, "No Match"  # 매칭 불가

    try:
        value = float(patient_data.iloc[0][column])  # 첫 번째 매칭 행에서 대상 컬럼 값을 숫자로 캐스팅
        actual_value = value  # 디버깅/가독성을 위한 보관(로직상 반환은 value로 충분)

        if pd.isna(value):  # 값이 NaN이면
            return value, "Invalid"  # 값 자체가 유효하지 않음

        # 항상 작은 쪽이 min, 큰 쪽이 max 되도록 — 사용자가 min/max를 바꿔 넣어도 안전하게
        lower = min(min_val, max_val)  # 두 값 중 더 작은 값을 하한으로
        upper = max(min_val, max_val)  # 두 값 중 더 큰 값을 상한으로

        if lower <= value <= upper:  # 하한 이상 상한 이하이면
            return value, "PASS"     # Pass
        else:
            return value, "FAIL"     # 범위를 벗어나면 Fail

    except Exception:  # 숫자 변환 실패, 키 에러 등 예외 발생 시
        return None, "Invalid"  # 값이 비정상적이므로 Invalid 처리


def compare_data(csv_df: pd.DataFrame, answer_df: pd.DataFrame):  # CSV 데이터와 정답 데이터를 비교하는 상위 함수
    """
    원본 스크립트의 6~8단계 로직을 함수로 재현.
    - 각 로우 validate 후 Engine_raw_vol_actual / Result 컬럼 생성
    - '엑셀에는 있는데 CSV에 아예 없는 session_id' 처리 등은
      원본 스크립트가 T1 볼류메트리 기준에서 정의하지 않았으므로 그대로 생략.
    반환: (results_df, rois)
    """
    actuals = []  # 각 행별 실제 측정값(Engine_raw_vol_actual)을 담을 리스트
    results = []  # 각 행별 판정 결과(Result: PASS/FAIL/No Match/Invalid)를 담을 리스트

    # answer_df 각 행 비교 — 정답지의 각 로우를 순회
    for _, row in answer_df.iterrows():         # 인덱스는 사용하지 않으므로 _로 버림
        value, result = _validate_row(row, csv_df)  # 위의 검증 함수 호출
        actuals.append(value)                        # 실제값 누적
        results.append(result)                       # 결과 누적

    out_df = answer_df.copy()  # 원본 손상 방지를 위해 복사본 생성
    out_df["Engine_raw_vol_actual"] = actuals  # 실제 측정값 컬럼 추가
    out_df["Result"] = results                 # 결과 컬럼 추가

    # rois: display_name 유니크 리스트(공통 시그니처 호환용) — 시각화/요약 등에 활용
    rois = (
        sorted(out_df["display_name"].dropna().unique().tolist())  # display_name 존재 시: 중복 제거 후 정렬
        if "display_name" in out_df.columns else []                 # 컬럼 자체가 없으면 빈 리스트
    )

    return out_df, rois  # 비교 결과 데이터프레임과 ROI 목록 반환
