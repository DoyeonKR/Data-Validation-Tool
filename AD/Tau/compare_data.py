import pandas as pd

def normalize_id_fixed(id_value):
    """Normalize an ID to lower case and strip whitespace."""
    return id_value.strip().lower()

def compare_data(csv_df, excel_df_filtered):
    """
    Compare data between CSV and Excel based on normalized IDs and calculate results.
    """
    # Add normalized IDs to both dataframes
    csv_df['Normalized Patient ID'] = csv_df['Patient ID'].apply(normalize_id_fixed)
    excel_df_filtered['Normalized Session ID'] = excel_df_filtered['session_id'].apply(normalize_id_fixed)

    rois = [
        'Total Neocortical Region SUVR',
        'Left Neocortical Region SUVR',
        'Right Neocortical Region SUVR',
        'Total Frontal Region SUVR',
        'Left Frontal Region SUVR',
        'Right Frontal Region SUVR',
    ]

    results_dict = {}
    for index, excel_row in excel_df_filtered.iterrows():
        session_id = excel_row['Normalized Session ID']

        # Match Patient ID with exact matching
        matching_patient_rows = csv_df[csv_df['Normalized Patient ID'] == session_id]

        if matching_patient_rows.empty:
            # No match found, record as 'No Match'
            if session_id not in results_dict:
                results_dict[session_id] = {
                    'Session ID': session_id,
                    'Patient ID': 'No Match',
                    'Overall Result': 'No Match',
                }
            continue

        # Process each matched patient
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
                    (excel_df_filtered['Normalized Session ID'] == session_id) &
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
                    mean_value = roi_matches['Engine_raw_vol_mean'].values[0]

                    if min_value <= volume_value <= max_value:
                        roi_result = 'Pass'
                    else:
                        roi_result = 'Fail'
                        overall_result = 'Fail'

                    patient_result[f'{roi} Result'] = roi_result
                    patient_result[f'{roi} min'] = min_value
                    patient_result[f'{roi} system'] = volume_value
                    patient_result[f'{roi} max'] = max_value
                    patient_result[f'{roi} Differ'] = volume_value - mean_value

            patient_result['Overall Result'] = overall_result


    # Convert results to DataFrame
    results_df = pd.DataFrame.from_dict(results_dict, orient='index')

    # 컬럼 순서 변경: 'Patient ID' 뒤에 'Overall Result'를 배치
    columns = list(results_df.columns)
    columns.remove('Overall Result')  # 'Overall Result' 제거
    columns.insert(columns.index('Patient ID') + 1, 'Overall Result')  # 'Patient ID' 뒤에 추가
    results_df = results_df[columns]

    return results_df, rois
