import pandas as pd

# ROI 번호와 CSV 컬럼명 매핑
ROI_MAPPING = {
    300: "Intracranial Volume(ICV)_Total Volume(Raw)",
    12: "Hippocampus_Total Volume(Raw)",
    112: "Hippocampus_Left Volume(Raw)",
    212: "Hippocampus_Right Volume(Raw)",
    5: "Inferior Lateral Ventricle_Total Volume(Raw)",
    105: "Inferior Lateral Ventricle_Left Volume(Raw)",
    205: "Inferior Lateral Ventricle_Right Volume(Raw)",
    307: "Lateral Ventricle_Total Volume(Raw)",
    407: "Lateral Ventricle_Left Volume(Raw)",
    507: "Lateral Ventricle_Right Volume(Raw)",
    3: "Cortical Grey Matter_Total Volume(Raw)",
    103: "Cortical Grey Matter_Left Volume(Raw)",
    203: "Cortical Grey Matter_Right Volume(Raw)",
    309: "Subcortical Grey Matter_Total Volume(Raw)",
    409: "Subcortical Grey Matter_Left Volume(Raw)",
    509: "Subcortical Grey Matter_Right Volume(Raw)"
}

# ID 정규화 함수
def normalize_id(id_value):
    return ''.join(str(id_value).strip().lower().replace('_', '').replace('-', ''))

# session_id에서 숫자 추출
def extract_id(session_id):
    parts = str(session_id).strip().split('_')
    for part in parts:
        if part.lower().startswith('s') and len(part) > 1:
            return part
        elif part.isdigit():
            return part
    return session_id.strip()

# 메인 비교 함수
def compare_data(csv_df, excel_df_filtered):
    # CSV 컬럼 정리
    csv_df.columns = [col.strip().replace('\u200b', '').replace('\xa0', ' ') for col in csv_df.columns]

    # 실제 비교할 수 있는 ROI만 필터링
    available_rois = {idx: name for idx, name in ROI_MAPPING.items() if name in csv_df.columns}
    rois = list(available_rois.values())

    results_dict = {}

    # Normalize Patient ID
    csv_df['Normalized Patient ID'] = csv_df['Patient ID'].apply(normalize_id)

    # 세션별 그룹
    grouped_excel = excel_df_filtered.groupby('session_id')

    for session_id, roi_rows in grouped_excel:
        session_id = str(session_id).strip()
        extracted_session_id = extract_id(session_id)
        normalized_session_id = normalize_id(extracted_session_id)

        # 환자 매칭
        matching_patient_rows = csv_df[csv_df['Normalized Patient ID'].str.contains(normalized_session_id, na=False)]

        if matching_patient_rows.empty:
            results_dict[session_id] = {
                'Session ID': session_id,
                'Patient ID': 'No Match',
                'Overall Result': 'No Match'
            }
            continue

        for _, patient_row in matching_patient_rows.iterrows():
            patient_id = patient_row['Patient ID'].strip()
            if patient_id not in results_dict:
                results_dict[patient_id] = {
                    'Session ID': session_id,
                    'Patient ID': patient_id
                }

            patient_result = results_dict[patient_id]
            overall_result = 'Pass'

            for _, roi_row in roi_rows.iterrows():
                roi_index = roi_row['roi_index']
                if roi_index not in available_rois:
                    continue

                roi_name = available_rois[roi_index]

                try:
                    system_value = float(patient_row[roi_name])
                except (KeyError, ValueError, TypeError):
                    patient_result[f'{roi_name} Result'] = 'No Match'
                    patient_result[f'{roi_name} min'] = 'None'
                    patient_result[f'{roi_name} system'] = 'None'
                    patient_result[f'{roi_name} max'] = 'None'
                    patient_result[f'{roi_name} Differ'] = 'None'
                    overall_result = 'Fail'
                    continue

                min_value = roi_row['Engine_raw_vol_min']
                max_value = roi_row['Engine_raw_vol_max']
                mean_value = roi_row['Engine_raw_vol_mean']

                if pd.isnull(min_value) or pd.isnull(max_value):
                    roi_result = 'No Match'
                elif min_value <= system_value <= max_value:
                    roi_result = 'Pass'
                else:
                    roi_result = 'Fail'
                    overall_result = 'Fail'

                patient_result[f'{roi_name} Result'] = roi_result
                patient_result[f'{roi_name} min'] = min_value
                patient_result[f'{roi_name} system'] = system_value
                patient_result[f'{roi_name} max'] = max_value
                patient_result[f'{roi_name} Differ'] = system_value - mean_value if pd.notnull(mean_value) else None

            patient_result['Overall Result'] = overall_result

    results_df = pd.DataFrame.from_dict(results_dict, orient='index')

    # 누락된 컬럼 보완
    for roi in rois:
        for suffix in ['Result', 'min', 'system', 'max', 'Differ']:
            col = f'{roi} {suffix}'
            if col not in results_df.columns:
                results_df[col] = 'None' if suffix != 'Differ' else None

    return results_df, rois
