# AD30/ARIAH/compare_data.py
import pandas as pd
from AD20.ARIAH.core import (
    create_location_key_mapping,
    extract_csv_coordinates,
    compare_coordinates,
    find_missing_in_csv,
)

def compare_data(csv_data: pd.DataFrame, txt_data: pd.DataFrame):
    """
    process_comparison 단계 2:
    - 원본 main() 로직을 동일하게 수행하여 results_df 생성
    - 반환: (results_df, rois)
    """
    location_mapping = create_location_key_mapping()

    # 정답지 기준, 좌표가 전혀 없는 session_id 목록 생성 (원본과 동일)
    coord_cols = [col for col in txt_data.columns if any(axis in str(col) for axis in ['x', 'y', 'z'])]
    if coord_cols:
        empty_sessions = (
            txt_data[coord_cols]
            .isna()
            .groupby(txt_data['session_id'])
            .all()
            .all(axis=1)
        )
        no_coord_sessions = set(empty_sessions[empty_sessions == True].index)
    else:
        no_coord_sessions = set()

    all_results = []

    # CSV의 각 환자별 처리
    for _, csv_row in csv_data.iterrows():
        patient_id = str(csv_row.get('Patient ID', '')).strip()
        if not patient_id:
            continue

        matching_txt = txt_data[txt_data['session_id'].astype(str).str.strip() == patient_id]

        csv_coordinates = extract_csv_coordinates(csv_row)

        # 정답지도 없고 CSV에도 없음 → pass
        if patient_id in no_coord_sessions and not csv_coordinates:
            all_results.append({
                'Patient_ID': patient_id,
                'CSV_Index': None,
                'Location': None,
                'App_X': None,
                'App_Y': None,
                'App_Z': None,
                'TechOps_X': None,
                'TechOps_Y': None,
                'TechOps_Z': None,
                'Result': 'Pass'
            })
            continue

        if matching_txt.empty:
            all_results.append({
                'Patient_ID': patient_id,
                'CSV_Index': None,
                'Location': None,
                'App_X': None,
                'App_Y': None,
                'App_Z': None,
                'TechOps_X': None,
                'TechOps_Y': None,
                'TechOps_Z': None,
                'Result': 'No Match',
                'details': 'No matching session_id found'
            })
            continue

        if not csv_coordinates:
            all_results.append({
                'Patient_ID': patient_id,
                'CSV_Index': None,
                'Location': None,
                'App_X': None,
                'App_Y': None,
                'App_Z': None,
                'TechOps_X': None,
                'TechOps_Y': None,
                'TechOps_Z': None,
                'Result': 'No Data',
                'details': 'No coordinate data in CSV'
            })
            continue

        txt_coordinates = matching_txt[['index', 'key', 'x', 'y', 'z']].to_dict('records')

        # 좌표 비교 (원본 함수 호출)
        comparison_results = compare_coordinates(csv_coordinates, txt_coordinates, location_mapping)

        # 비교 결과 적재 (필드명도 원본과 동일)
        for comp in comparison_results:
            all_results.append({
                'Patient_ID': patient_id,
                'CSV_Index': comp['csv_index'],
                'Location': comp['location'],
                'App_X': comp['csv_x'],
                'App_Y': comp['csv_y'],
                'App_Z': comp['csv_z'],
                'TechOps_X': comp['txt_x'],
                'TechOps_Y': comp['txt_y'],
                'TechOps_Z': comp['txt_z'],
                'Result': comp['result']
            })

        # Excel에는 있으나 CSV에 없는 index 처리 (원본 함수 호출)
        missing_results = find_missing_in_csv(csv_coordinates, txt_coordinates, patient_id, location_mapping)
        all_results.extend(missing_results)

    # ✅ 엑셀에는 있는데 CSV에 아예 없는 session_id 처리 (원본과 동일)
    csv_patient_ids = set(csv_data.get('Patient ID').dropna().astype(str).str.strip()) if 'Patient ID' in csv_data.columns else set()
    excel_session_ids = set(txt_data.get('session_id').dropna().astype(str).str.strip()) if 'session_id' in txt_data.columns else set()

    missing_in_csv_ids = excel_session_ids - csv_patient_ids
    for missing_id in missing_in_csv_ids:
        all_results.append({
            'Patient_ID': missing_id,
            'CSV_Index': None,
            'Location': None,
            'App_X': None,
            'App_Y': None,
            'App_Z': None,
            'TechOps_X': None,
            'TechOps_Y': None,
            'TechOps_Z': None,
            'Result': 'Missing in CSV entirely'
        })

    results_df = pd.DataFrame(all_results)

    # rois: 공통 시그니처 호환용(스타일링 등에 쓰일 수 있음) — 여기선 Location의 유니크값 정도로 반환
    rois = sorted(results_df['Location'].dropna().unique().tolist()) if 'Location' in results_df.columns else []

    return results_df, rois
