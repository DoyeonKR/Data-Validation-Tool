import pandas as pd

# ROI 번호와 CSV 컬럼명 매핑
ROI_MAPPING = {
    908: "Periventricular FLAIR Hyperintensity _Volume",
    907: "Deep FLAIR Hyperintensity _Volume",
    909: "Subcortical Grey Matter FLAIR Hyperintensity _Volume"
}


def extract_id(session_id):
    """session_id에서 ID 부분만 추출하는 함수.

    Args:
        session_id (str): 세션 ID (예: 'sub_1234_20240101')

    Returns:
        str: 추출된 ID 부분 (예: '1234')
    """
    parts = session_id.split('_')
    if len(parts) > 1:
        return parts[1]
    return session_id


def normalize_id(id_value):
    """ID를 표준 형식으로 변환하는 함수.

    Args:
        id_value (str): 원본 ID 값

    Returns:
        str: 소문자로 변환하고 언더스코어 제거한 정규화된 ID
    """
    return ''.join(id_value.lower().split('_'))


def compare_data(csv_df, excel_df_filtered):
    """CSV와 Excel 데이터를 비교하여 결과를 반환하는 메인 함수.

    Args:
        csv_df (DataFrame): CSV 파일에서 로드한 데이터프레임
        excel_df_filtered (DataFrame): Excel 파일에서 필터링된 데이터프레임

    Returns:
        tuple: (결과 데이터프레임, ROI 리스트)
    """
    # CSV 컬럼명 정리 - 불필요한 공백 및 특수문자 제거
    csv_df.columns = [col.strip().replace('\u200b', '').replace('\xa0', ' ') for col in csv_df.columns]

    # 실제 CSV에 존재하는 ROI만 필터링하여 비교 대상 결정
    available_rois = {idx: name for idx, name in ROI_MAPPING.items() if name in csv_df.columns}
    rois = list(available_rois.values())

    # 비교 결과를 저장할 딕셔너리
    results_dict = {}

    # CSV 데이터의 Patient ID 정규화
    csv_df['Normalized Patient ID'] = csv_df['Patient ID'].apply(normalize_id)

    # Excel 데이터를 session_id별로 그룹화 (한 세션에 여러 ROI 데이터 존재)
    grouped_excel = excel_df_filtered.groupby('session_id')

    # 각 세션별로 처리
    for session_id, roi_rows in grouped_excel:
        # 세션 ID 전처리
        session_id = str(session_id).strip()
        extracted_session_id = extract_id(session_id)  # ID 부분만 추출
        normalized_session_id = normalize_id(extracted_session_id)  # 정규화

        # CSV에서 해당 세션과 매칭되는 환자 찾기
        matching_patient_rows = csv_df[csv_df['Normalized Patient ID'].str.contains(normalized_session_id, na=False)]

        # 매칭되는 환자가 없는 경우
        if matching_patient_rows.empty:
            results_dict[session_id] = {
                'Session ID': session_id,
                'Patient ID': 'No Match',
                'Overall Result': 'No Match'
            }
            continue

        # 매칭된 환자들에 대해 처리
        for _, patient_row in matching_patient_rows.iterrows():
            patient_id = patient_row['Patient ID'].strip()

            # 결과 딕셔너리에 환자 정보 초기화
            if patient_id not in results_dict:
                results_dict[patient_id] = {
                    'Session ID': session_id,
                    'Patient ID': patient_id
                }

            patient_result = results_dict[patient_id]
            overall_result = 'Pass'  # 전체 결과 초기값

            # 해당 세션의 각 ROI 데이터 처리
            for _, roi_row in roi_rows.iterrows():
                roi_index = roi_row['roi_index']  # ROI 번호

                # 매핑되지 않은 ROI는 건너뛰기
                if roi_index not in available_rois:
                    continue

                roi_name = available_rois[roi_index]  # ROI 이름 가져오기

                # CSV에서 해당 ROI 값 추출 시도
                try:
                    system_value = float(patient_row[roi_name])
                except (KeyError, ValueError, TypeError):
                    # 값을 가져오지 못한 경우 'No Match' 처리
                    patient_result[f'{roi_name} Result'] = 'No Match'
                    patient_result[f'{roi_name} min'] = 'None'
                    patient_result[f'{roi_name} system'] = 'None'
                    patient_result[f'{roi_name} max'] = 'None'
                    patient_result[f'{roi_name} Differ'] = 'None'
                    overall_result = 'Fail'
                    continue

                # Excel에서 해당 ROI의 참조 범위 값들 가져오기
                min_value = roi_row['Engine_raw_vol_min']
                max_value = roi_row['Engine_raw_vol_max']
                mean_value = roi_row['Engine_raw_vol_mean']

                # 참조 범위가 유효한지 확인하고 비교 수행
                if pd.isnull(min_value) or pd.isnull(max_value):
                    roi_result = 'No Match'  # 참조 범위가 없는 경우
                elif min_value <= system_value <= max_value:
                    roi_result = 'Pass'  # 범위 내에 있는 경우
                else:
                    roi_result = 'Fail'  # 범위를 벗어난 경우
                    overall_result = 'Fail'  # 하나라도 실패하면 전체 실패

                # 결과 저장
                patient_result[f'{roi_name} Result'] = roi_result
                patient_result[f'{roi_name} min'] = min_value
                patient_result[f'{roi_name} system'] = system_value
                patient_result[f'{roi_name} max'] = max_value
                # 평균값과의 차이 계산
                patient_result[f'{roi_name} Differ'] = system_value - mean_value if pd.notnull(mean_value) else None

            # 해당 환자의 전체 결과 저장
            patient_result['Overall Result'] = overall_result

    # 딕셔너리를 데이터프레임으로 변환
    results_df = pd.DataFrame.from_dict(results_dict, orient='index')

    # 누락된 컬럼들을 기본값으로 보완 (모든 ROI에 대해 일관된 컬럼 구조 보장)
    for roi in rois:
        for suffix in ['Result', 'min', 'system', 'max', 'Differ']:
            col = f'{roi} {suffix}'
            if col not in results_df.columns:
                results_df[col] = 'None' if suffix != 'Differ' else None

    return results_df, rois

