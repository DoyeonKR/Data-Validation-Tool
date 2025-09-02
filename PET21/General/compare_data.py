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
        'Total Cerebral Cortex SUVR',
        'Left Cerebral Cortex SUVR',
        'Right Cerebral Cortex SUVR',
        'Total Frontal Cortex SUVR',
        'Left Frontal Cortex SUVR',
        'Right Frontal Cortex SUVR',
        'Total Caudal Middle Frontal SUVR',
        'Left Caudal Middle Frontal SUVR',
        'Right Caudal Middle Frontal SUVR',
        'Total Lateral Orbitofrontal SUVR',
        'Left Lateral Orbitofrontal SUVR',
        'Right Lateral Orbitofrontal SUVR',
        'Total Medial Orbitofrontal SUVR',
        'Left Medial Orbitofrontal SUVR',
        'Right Medial Orbitofrontal SUVR',
        'Total Pars Opercularis SUVR',
        'Left Pars Opercularis SUVR',
        'Right Pars Opercularis SUVR',
        'Total Pars Orbitalis SUVR',
        'Left Pars Orbitalis SUVR',
        'Right Pars Orbitalis SUVR',
        'Total Pars Triangularis SUVR',
        'Left Pars Triangularis SUVR',
        'Right Pars Triangularis SUVR',
        'Total Rostral Middle Frontal SUVR',
        'Left Rostral Middle Frontal SUVR',
        'Right Rostral Middle Frontal SUVR',
        'Total Superior Frontal SUVR',
        'Left Superior Frontal SUVR',
        'Right Superior Frontal SUVR',
        'Total Frontal Pole SUVR',
        'Left Frontal Pole SUVR',
        'Right Frontal Pole SUVR',
        'Total Precentral SUVR',
        'Left Precentral SUVR',
        'Right Precentral SUVR',
        'Total Paracentral SUVR',
        'Left Paracentral SUVR',
        'Right Paracentral SUVR',
        'Total Parietal Cortex SUVR',
        'Left Parietal Cortex SUVR',
        'Right Parietal Cortex SUVR',
        'Total Inferior Parietal SUVR',
        'Left Inferior Parietal SUVR',
        'Right Inferior Parietal SUVR',
        'Total Precuneus SUVR',
        'Left Precuneus SUVR',
        'Right Precuneus SUVR',
        'Total Superior Parietal SUVR',
        'Left Superior Parietal SUVR',
        'Right Superior Parietal SUVR',
        'Total Supramarginal SUVR',
        'Left Supramarginal SUVR',
        'Right Supramarginal SUVR',
        'Total Postcentral SUVR',
        'Left Postcentral SUVR',
        'Right Postcentral SUVR',
        'Total Temporal Cortex SUVR',
        'Left Temporal Cortex SUVR',
        'Right Temporal Cortex SUVR',
        'Total Middle Temporal SUVR',
        'Left Middle Temporal SUVR',
        'Right Middle Temporal SUVR',
        'Total Superior Temporal SUVR',
        'Left Superior Temporal SUVR',
        'Right Superior Temporal SUVR',
        'Total Posterior Transverse Temporal SUVR',
        'Left Posterior Transverse Temporal SUVR',
        'Right Posterior Transverse Temporal SUVR',
        'Total Entorhinal SUVR',
        'Left Entorhinal SUVR',
        'Right Entorhinal SUVR',
        'Total Fusiform SUVR',
        'Left Fusiform SUVR',
        'Right Fusiform SUVR',
        'Total Inferior Temporal SUVR',
        'Left Inferior Temporal SUVR',
        'Right Inferior Temporal SUVR',
        'Total Parahippocampal SUVR',
        'Left Parahippocampal SUVR',
        'Right Parahippocampal SUVR',
        'Total Temporal Pole SUVR',
        'Left Temporal Pole SUVR',
        'Right Temporal Pole SUVR',
        'Total Transverse Temporal SUVR',
        'Left Transverse Temporal SUVR',
        'Right Transverse Temporal SUVR',
        'Total Occipital Cortex SUVR',
        'Left Occipital Cortex SUVR',
        'Right Occipital Cortex SUVR',
        'Total Cuneus SUVR',
        'Left Cuneus SUVR',
        'Right Cuneus SUVR',
        'Total Lateral Occipital SUVR',
        'Left Lateral Occipital SUVR',
        'Right Lateral Occipital SUVR',
        'Total Lingual SUVR',
        'Left Lingual SUVR',
        'Right Lingual SUVR',
        'Total Pericalcarine SUVR',
        'Left Pericalcarine SUVR',
        'Right Pericalcarine SUVR',
        'Total Cingulate Cortex SUVR',
        'Left Cingulate Cortex SUVR',
        'Right Cingulate Cortex SUVR',
        'Total Caudal Anterior Cingulate SUVR',
        'Left Caudal Anterior Cingulate SUVR',
        'Right Caudal Anterior Cingulate SUVR',
        'Total Isthmus of Cingulate SUVR',
        'Left Isthmus of Cingulate SUVR',
        'Right Isthmus of Cingulate SUVR',
        'Total Posterior Cingulate SUVR',
        'Left Posterior Cingulate SUVR',
        'Right Posterior Cingulate SUVR',
        'Total Rostral Anterior Cingulate SUVR',
        'Left Rostral Anterior Cingulate SUVR',
        'Right Rostral Anterior Cingulate SUVR',
        'Total Subcortical Regions SUVR',
        'Left Subcortical Regions SUVR',
        'Right Subcortical Regions SUVR',
        'Total Caudate SUVR',
        'Left Caudate SUVR',
        'Right Caudate SUVR',
        'Total Putamen SUVR',
        'Left Putamen SUVR',
        'Right Putamen SUVR',
        'Total Thalamus SUVR',
        'Left Thalamus SUVR',
        'Right Thalamus SUVR',
        'Total Pallidum SUVR',
        'Left Pallidum SUVR',
        'Right Pallidum SUVR',
        'Total Hippocampus SUVR',
        'Left Hippocampus SUVR',
        'Right Hippocampus SUVR',
        'Total Amygdala SUVR',
        'Left Amygdala SUVR',
        'Right Amygdala SUVR',
        'Total Accumbens SUVR',
        'Left Accumbens SUVR',
        'Right Accumbens SUVR',
        'Total Cerebellum SUVR',
        'Left Cerebellum SUVR',
        'Right Cerebellum SUVR',
        'Total Cerebellum White Matter SUVR',
        'Left Cerebellum White Matter SUVR',
        'Right Cerebellum White Matter SUVR',
        'Total Cerebellum Grey Matter SUVR',
        'Left Cerebellum Grey Matter SUVR',
        'Right Cerebellum Grey Matter SUVR',
        'Total Brainstem SUVR',
        'Total Pons SUVR',
        'Total Insula Cortex SUVR',
        'Left Insula Cortex SUVR',
        'Right Insula Cortex SUVR',
        'Total Ventral Diencephalon SUVR',
        'Left Ventral Diencephalon SUVR',
        'Right Ventral Diencephalon SUVR',
        'Total Corpus Callosum SUVR',
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

    # DataFrame 반환 전에 컬럼 순서 변경 추가

    # Convert results to DataFrame
    results_df = pd.DataFrame.from_dict(results_dict, orient='index')

    # 컬럼 순서 변경: 'Patient ID' 뒤에 'Overall Result'를 배치
    columns = list(results_df.columns)
    columns.remove('Overall Result')  # 'Overall Result' 제거
    columns.insert(columns.index('Patient ID') + 1, 'Overall Result')  # 'Patient ID' 뒤에 추가
    results_df = results_df[columns]

    return results_df, rois

