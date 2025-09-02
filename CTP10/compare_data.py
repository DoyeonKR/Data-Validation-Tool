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
        'Tmax >1 sec Volume (mL)',
        'Tmax >2 sec Volume (mL)',
        'Tmax >4 sec Volume (mL)',
        'Tmax >6 sec Volume (mL)',
        'Tmax >8 sec Volume (mL)',
        'Tmax >10 sec Volume (mL)',
        'Tmax >12 sec Volume (mL)',
        'Tmax >14 sec Volume (mL)',
        'CBF <40% Volume (mL)',
        'CBF <38% Volume (mL)',
        'CBF <36% Volume (mL)',
        'CBF <34% Volume (mL)',
        'CBF <32% Volume (mL)',
        'CBF <30% Volume (mL)',
        'CBF <25% Volume (mL)',
        'CBF <20% Volume (mL)',
        'CBV <46% Volume (mL)',
        'CBV <44% Volume (mL)',
        'CBV <42% Volume (mL)',
        'CBV <40% Volume (mL)',
        'CBV <38% Volume (mL)',
        'CBV <36% Volume (mL)',
        'CBV <34% Volume (mL)',
        'CBV <32% Volume (mL)',
        'AIF Location',
        'VOF Location',
        'Mismatch Volume (mL)_Tmax Threhold Volume-CBF Threhold Volume',
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

                if 'Location' in roi:  # Location 항목 처리
                    try:
                        system_location = list(map(int, patient_row[roi].split(',')))  # CSV 좌표 분리
                    except (ValueError, AttributeError):
                        patient_result[f'{roi} Result'] = 'No Match'
                        patient_result[f'{roi} Expected'] = 'None'
                        patient_result[f'{roi} System'] = 'None'
                        overall_result = 'Fail'
                        continue

                    roi_matches = excel_df_filtered[
                        (excel_df_filtered['Normalized Session ID'] == session_id) &
                        (excel_df_filtered['roi_product_name'] == roi)
                    ]

                    if roi_matches.empty:
                        patient_result[f'{roi} Result'] = 'No Match'
                        patient_result[f'{roi} Expected'] = 'None'
                        patient_result[f'{roi} System'] = system_location
                        overall_result = 'Fail'
                    else:
                        try:
                            expected_location = list(map(int, roi_matches['Engine_raw_vol_mean'].values[0].split(',')))  # Excel 좌표 분리
                        except (ValueError, AttributeError):
                            patient_result[f'{roi} Result'] = 'No Match'
                            patient_result[f'{roi} Expected'] = 'None'
                            patient_result[f'{roi} System'] = system_location
                            overall_result = 'Fail'
                            continue

                        # 좌표 비교 (x, y, z 모두 일치해야 Pass)
                        if system_location == expected_location:
                            roi_result = 'Pass'
                        else:
                            roi_result = 'Fail'
                            overall_result = 'Fail'

                        # 결과 저장
                        patient_result[f'{roi} Result'] = roi_result
                        patient_result[f'{roi} Expected'] = expected_location
                        patient_result[f'{roi} System'] = system_location
                    continue  # Location 처리 후 다음 ROI로 넘어감

                else:  # 일반적인 수치 비교 처리 (음수 포함)
                    try:
                        volume_value = float(patient_row[roi])
                    except (ValueError, TypeError):
                        patient_result[f'{roi} Result'] = 'No Match'
                        patient_result[f'{roi} min'] = 'None'
                        patient_result[f'{roi} system'] = 'None'
                        patient_result[f'{roi} max'] = 'None'
                        overall_result = 'Fail'
                        continue

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
                        try:
                            min_value = float(roi_matches['Engine_raw_vol_min'].values[0])
                            max_value = float(roi_matches['Engine_raw_vol_max'].values[0])
                            mean_value = float(roi_matches['Engine_raw_vol_mean'].values[0])
                        except (ValueError, TypeError):
                            patient_result[f'{roi} Result'] = 'No Match'
                            patient_result[f'{roi} min'] = 'None'
                            patient_result[f'{roi} system'] = volume_value
                            patient_result[f'{roi} max'] = 'None'
                            overall_result = 'Fail'
                            continue

                        # Perform numeric comparison (including negative range handling)
                        if min(min_value, max_value) <= volume_value <= max(max_value, min_value):
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

    results_df = pd.DataFrame.from_dict(results_dict, orient='index')

    # 컬럼 순서 변경: 'Patient ID' 뒤에 'Overall Result'를 배치
    columns = list(results_df.columns)
    columns.remove('Overall Result')  # 'Overall Result' 제거
    columns.insert(columns.index('Patient ID') + 1, 'Overall Result')  # 'Patient ID' 뒤에 추가
    results_df = results_df[columns]

    return results_df, rois
