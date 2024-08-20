import pandas as pd

def extract_id(session_id):
    # session_id에서 ID 부분만 추출하는 함수
    parts = session_id.split('_')
    if len(parts) > 1:
        return parts[1]
    return session_id


def normalize_id(id_value):
    # ID를 표준 형식으로 변환하는 함수
    return ''.join(id_value.lower().split('_'))


def compare_data(csv_df, excel_df_filtered):
    rois = [
        'Periventricular FLAIR Hyperintensity _Volume',
        'Subcortical Grey Matter FLAIR Hyperintensity _Volume',
        'Total FLAIR Hyperintensity _Volume',
        'Deep FLAIR Hyperintensity _Volume',
    ]

    results_dict = {}
    for index, excel_row in excel_df_filtered.iterrows():
        session_id = excel_row['session_id'].strip()
        extracted_session_id = extract_id(session_id)
        normalized_session_id = normalize_id(extracted_session_id)

        # Patient ID를 표준 형식으로 변환한 후 비교
        csv_df['Normalized Patient ID'] = csv_df['Patient ID'].apply(normalize_id)
        matching_patient_rows = csv_df[csv_df['Normalized Patient ID'].str.contains(normalized_session_id, na=False)]

        # 매칭된 행을 출력하여 확인
        print(f"Matching rows for session ID {session_id} (normalized as {normalized_session_id}):")
        print(matching_patient_rows)

        if matching_patient_rows.empty:
            if session_id not in results_dict:
                results_dict[session_id] = {'Session ID': session_id, 'Patient ID': 'No Match',
                                            'Overall Result': 'No Match'}
            continue

        for _, patient_row in matching_patient_rows.iterrows():
            patient_id = patient_row['Patient ID'].strip()
            if patient_id not in results_dict:
                results_dict[patient_id] = {'Session ID': session_id, 'Patient ID': patient_id}

            overall_result = 'Pass'
            patient_result = results_dict[patient_id]

            for roi in rois:
                if roi not in patient_row:
                    patient_result[f'{roi} Result'] = 'No Match'
                    patient_result[f'{roi} min'] = 'None'
                    patient_result[f'{roi} system'] = 'None'
                    patient_result[f'{roi} max'] = 'None'
                    overall_result = 'Fail'
                    continue

                volume_value = patient_row[roi]

                roi_matches = excel_df_filtered[
                    (excel_df_filtered['session_id'] == session_id) &
                    (excel_df_filtered['roi_product_name'] == roi)
                    ]

                if roi_matches.empty:
                    patient_result[f'{roi} Result'] = 'No Match'
                    patient_result[f'{roi} min'] = 'None'
                    patient_result[f'{roi} system'] = 'None'
                    patient_result[f'{roi} max'] = 'None'
                    overall_result = 'Fail'
                else:
                    min_value = roi_matches['Engine_raw_vol_min'].values[0]
                    max_value = roi_matches['Engine_raw_vol_max'].values[0]

                    if min_value <= volume_value <= max_value:
                        roi_result = 'Pass'
                    else:
                        roi_result = 'Fail'
                        overall_result = 'Fail'

                    patient_result[f'{roi} Result'] = roi_result
                    patient_result[f'{roi} min'] = min_value
                    patient_result[f'{roi} system'] = volume_value
                    patient_result[f'{roi} max'] = max_value

            patient_result['Overall Result'] = overall_result

    results_df = pd.DataFrame.from_dict(results_dict, orient='index')
    return results_df, rois

