import pandas as pd
from tqdm import tqdm


def normalize_id_fixed(id_value):
    """Normalize an ID to lower case, strip whitespace, and remove date suffix."""
    # 날짜 부분 제거 (마지막 _YYYYMMDD 형태)
    clean_id = id_value.strip().lower()
    # 마지막 _ 이후가 8자리 숫자면 날짜로 간주하고 제거
    parts = clean_id.split('_')
    if len(parts) > 2 and len(parts[-1]) == 8 and parts[-1].isdigit():
        clean_id = '_'.join(parts[:-1])
    return clean_id


def compare_data(csv_df, excel_df_filtered):
    """
    Compare data between CSV and Excel based on normalized IDs and calculate results.
    """
    # ID 정규화 + 비교 정확도 보장
    csv_df['Normalized Patient ID'] = csv_df['Patient ID'].apply(normalize_id_fixed).astype(str).str.strip().str.lower()
    excel_df_filtered['Normalized Session ID'] = excel_df_filtered['session_id'].apply(normalize_id_fixed).astype(str).str.strip().str.lower()

    rois = [
        'Centiloid scale',
        'Total Regions of Interest for Amyloid PET SUVR',
        'Left Regions of Interest for Amyloid PET SUVR',
        'Right Regions of Interest for Amyloid PET SUVR',
        'Total Frontal Target Region SUVR',
        'Left Frontal Target Region SUVR',
        'Right Frontal Target Region SUVR',
        'Total Lateral Parietal Target Region SUVR',
        'Left Lateral Parietal Target Region SUVR',
        'Right Lateral Parietal Target Region SUVR',
        'Total Precuneus SUVR',
        'Left Precuneus SUVR',
        'Right Precuneus SUVR',
        'Total Lateral Temporal Target Region SUVR',
        'Left Lateral Temporal Target Region SUVR',
        'Right Lateral Temporal Target Region SUVR',
        'Total Cingulate Cortex SUVR',
        'Left Cingulate Cortex SUVR',
        'Right Cingulate Cortex SUVR',
        'Total Striatum SUVR',
        'Left Striatum SUVR',
        'Right Striatum SUVR',
    ]

    results_dict = {}

    print(f"총 {len(excel_df_filtered)}개 행 처리 시작...")

    for index, excel_row in tqdm(excel_df_filtered.iterrows(), total=len(excel_df_filtered), desc="데이터 비교 중"):
        session_id = excel_row['Normalized Session ID']

        # 정확한 비교 수행
        matching_patient_rows = csv_df[csv_df['Normalized Patient ID'] == session_id]

        if matching_patient_rows.empty:
            if session_id not in results_dict:
                results_dict[session_id] = {
                    'Session ID': session_id,
                    'Patient ID': 'No Match',
                    'Overall Result': 'No Match',
                }
            continue

        for _, patient_row in matching_patient_rows.iterrows():
            patient_id = patient_row['Patient ID'].strip()
            if patient_id not in results_dict:
                results_dict[patient_id] = {
                    'Session ID': session_id,
                    'Patient ID': patient_id
                }

            overall_result = 'Pass'
            patient_result = results_dict[patient_id]

            for roi in rois:
                if roi not in patient_row:
                    patient_result[f'{roi} Result'] = 'No Match'
                    patient_result[f'{roi} min'] = 'None'
                    patient_result[f'{roi} system'] = 'None'
                    patient_result[f'{roi} max'] = 'None'
                    patient_result[f'{roi} Differ'] = 'None'
                    overall_result = 'Fail'
                    continue

                volume_value = patient_row[roi]

                roi_matches = excel_df_filtered[
                    (excel_df_filtered['Normalized Session ID'] == session_id) &
                    (excel_df_filtered['roi_product_name'] == roi)
                ]

                if roi_matches.empty:
                    patient_result[f'{roi} Result'] = 'No Match'
                    patient_result[f'{roi} min'] = 'None'
                    patient_result[f'{roi} system'] = 'None'
                    patient_result[f'{roi} max'] = 'None'
                    patient_result[f'{roi} Differ'] = 'None'
                    overall_result = 'Fail'
                else:
                    try:
                        lower_bound = float(roi_matches['Engine_raw_vol_min'].values[0])
                        upper_bound = float(roi_matches['Engine_raw_vol_max'].values[0])
                        mean_value = float(roi_matches['Engine_raw_vol_mean'].values[0])
                        volume_value_float = float(volume_value)

                        # 음수 정렬 포함한 범위 보장
                        lower_bound, upper_bound = sorted([lower_bound, upper_bound])

                        if lower_bound <= volume_value_float <= upper_bound:
                            roi_result = 'Pass'
                        else:
                            roi_result = 'Fail'
                            overall_result = 'Fail'

                        difference = volume_value_float - mean_value

                    except (ValueError, TypeError):
                        roi_result = 'Error'
                        overall_result = 'Fail'
                        lower_bound = 'Error'
                        upper_bound = 'Error'
                        mean_value = 'Error'
                        difference = 'Error'

                    patient_result[f'{roi} Result'] = roi_result
                    patient_result[f'{roi} min'] = lower_bound
                    patient_result[f'{roi} system'] = volume_value
                    patient_result[f'{roi} max'] = upper_bound
                    patient_result[f'{roi} Differ'] = difference

            patient_result['Overall Result'] = overall_result

    print("✅ 데이터 비교 완료!")

    results_df = pd.DataFrame.from_dict(results_dict, orient='index')

    # 컬럼 순서 재배열
    columns = list(results_df.columns)
    columns.remove('Overall Result')
    columns.insert(columns.index('Patient ID') + 1, 'Overall Result')
    results_df = results_df[columns]

    return results_df, rois
