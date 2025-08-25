import pandas as pd
import re
import datetime


def load_and_prepare_data():
    """데이터 파일들을 로드하고 전처리"""

    # CSV 파일 읽기
    try:
        csv_data = pd.read_csv('ARIA-H (Microhemorrhage)_2025-07-28.csv')
        print(f"CSV 파일 로드 완료: {len(csv_data)} 행")
    except Exception as e:
        print(f"CSV 파일 로드 오류: {e}")
        return None, None


    try:
        excel_data = pd.read_excel('250730_ARIA_H_v122.xlsx')
        print(f"엑셀 파일 로드 완료: {len(excel_data)} 행")
    except Exception as e:
        print(f"엑셀 파일 로드 오류: {e}")
        return None, None

    return csv_data, excel_data


def create_location_key_mapping():
    """Location과 Key 매핑 딕셔너리 생성"""
    return {
        428: 'Lt_Frontal',
        528: 'Rt_Frontal',
        429: 'Lt_Temporal',
        529: 'Rt_Temporal',
        430: 'Lt_Parietal',
        530: 'Rt_Parietal',
        431: 'Lt_Occipital',
        531: 'Rt_Occipital',
        406: 'Lt_Cerebellum',
        506: 'Rt_Cerebellum',
        97: 'Brainstem',
        0: 'Others'
    }


def extract_csv_coordinates(csv_row):
    """CSV 행에서 좌표 데이터 추출"""
    coordinates = []

    coordinate_pattern = r'^(\d+) ([xyz]) coordinate$'

    indices = set()
    for col in csv_row.index:
        match = re.match(coordinate_pattern, str(col))
        if match:
            indices.add(int(match.group(1)))

    for idx in sorted(indices):
        x_col = f"{idx} x coordinate"
        y_col = f"{idx} y coordinate"
        z_col = f"{idx} z coordinate"
        location_col = f"{idx} location"

        x = csv_row.get(x_col)
        y = csv_row.get(y_col)
        z = csv_row.get(z_col)
        location = csv_row.get(location_col)

        # Null 문자열 또는 NaN 필터링
        if (
            pd.isna(x) or pd.isna(y) or pd.isna(z) or pd.isna(location) or
            str(x).strip().lower() == "null" or
            str(y).strip().lower() == "null" or
            str(z).strip().lower() == "null" or
            str(location).strip().lower() == "null"
        ):
            continue

        coordinates.append({
            'index': idx,
            'x': x,
            'y': y,
            'z': z,
            'location': location
        })

    return coordinates



def compare_coordinates(csv_coords, txt_coords, location_mapping):
    """
    CSV 좌표 리스트와 엑셀 좌표 리스트를 index 기준으로 매칭하여 좌표 값을 비교합니다.

    Parameters:
        csv_coords (list of dict): CSV에서 추출된 좌표들
        txt_coords (list of dict): Excel에서 추출된 좌표들 (key 포함)
        location_mapping (dict): Key → Location 매핑

    Returns:
        list of dict: 비교 결과 리스트
    """

    results = []

    for csv_coord in csv_coords:
        csv_index = csv_coord['index']
        csv_location = csv_coord['location']

        try:
            csv_x = float(csv_coord['x'])
            csv_y = float(csv_coord['y'])
            csv_z = float(csv_coord['z'])
        except (ValueError, TypeError):
            results.append({
                'csv_index': csv_index,
                'location': csv_location,
                'csv_x': csv_coord['x'],
                'csv_y': csv_coord['y'],
                'csv_z': csv_coord['z'],
                'txt_x': None,
                'txt_y': None,
                'txt_z': None,
                'result': 'Invalid CSV Value'
            })
            continue

        # index 기준으로 Excel 좌표 찾기
        matched_txt = next((txt for txt in txt_coords if txt['index'] == csv_index), None)

        if matched_txt is None:
            results.append({
                'csv_index': csv_index,
                'location': csv_location,
                'csv_x': csv_x,
                'csv_y': csv_y,
                'csv_z': csv_z,
                'txt_x': None,
                'txt_y': None,
                'txt_z': None,
                'result': 'No Match by Index'
            })
            continue

        try:
            txt_x = float(matched_txt['x'])
            txt_y = float(matched_txt['y'])
            txt_z = float(matched_txt['z'])
            txt_key = int(matched_txt['key'])
            txt_location = location_mapping.get(txt_key, 'Unknown')
        except (ValueError, TypeError):
            results.append({
                'csv_index': csv_index,
                'location': csv_location,
                'csv_x': csv_x,
                'csv_y': csv_y,
                'csv_z': csv_z,
                'txt_x': matched_txt.get('x'),
                'txt_y': matched_txt.get('y'),
                'txt_z': matched_txt.get('z'),
                'result': 'Invalid Excel Value'
            })
            continue

        x_match = abs(csv_x - txt_x) < 0.001
        y_match = abs(csv_y - txt_y) < 0.001
        z_match = abs(csv_z - txt_z) < 0.001
        location_match = (csv_location == txt_location)

        if x_match and y_match and z_match and location_match:
            result = 'Pass'
        elif not location_match:
            result = 'Location Mismatch'
        else:
            result = 'Fail'

        results.append({
            'csv_index': csv_index,
            'location': csv_location,
            'csv_x': csv_x,
            'csv_y': csv_y,
            'csv_z': csv_z,
            'txt_x': txt_x,
            'txt_y': txt_y,
            'txt_z': txt_z,
            'result': result
        })

    return results


from datetime import datetime

def find_missing_in_csv(csv_coords, txt_coords, patient_id, location_mapping):
    csv_index_set = {coord['index'] for coord in csv_coords if pd.notna(coord['index'])}
    txt_index_set = {int(txt['index']) for txt in txt_coords if pd.notna(txt['index'])}

    missing_results = []
    for idx in txt_index_set - csv_index_set:
        matched_txt = next((txt for txt in txt_coords if pd.notna(txt['index']) and int(txt['index']) == idx), None)
        if matched_txt:
            key = int(matched_txt['key']) if pd.notna(matched_txt['key']) else None
            missing_results.append({
                'Patient_ID': patient_id,
                'CSV_Index': idx,
                'Location': location_mapping.get(key, 'Unknown') if key is not None else 'Unknown',
                'APP_X': None,
                'APP_Y': None,
                'APP_Z': None,
                'TechOps_X': matched_txt['x'],
                'TechOps_Y': matched_txt['y'],
                'TechOps_Z': matched_txt['z'],
                'Result': 'Missing in CSV'
            })
    return missing_results



def main():
    """메인 실행 함수"""
    print("=== CSV vs Excel ARIA H 파일 비교 도구 ===\n")

    # 데이터 로드
    csv_data, txt_data = load_and_prepare_data()
    if csv_data is None or txt_data is None:
        return

    # 매핑 테이블 생성
    location_mapping = create_location_key_mapping()

    # 정답지 기준, 좌표가 전혀 없는 session_id 목록 생성
    coord_cols = [col for col in txt_data.columns if any(axis in col for axis in ['x', 'y', 'z'])]
    empty_sessions = (
        txt_data[coord_cols]
        .isna()
        .groupby(txt_data['session_id'])
        .all()
        .all(axis=1)
    )
    no_coord_sessions = set(empty_sessions[empty_sessions == True].index)

    # 결과 저장용 리스트
    all_results = []

    print(f"\n비교 시작...")

    # CSV의 각 환자별로 처리
    for idx, csv_row in csv_data.iterrows():
        patient_id = csv_row['Patient ID']
        print(f"처리 중: {patient_id}")

        # TXT에서 매칭되는 session_id 찾기
        matching_txt = txt_data[txt_data['session_id'] == patient_id]

        # 정답지도 없고 CSV에도 없음 → pass
        csv_coordinates = extract_csv_coordinates(csv_row)
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
                'result': 'No Match',
                'details': 'No matching session_id found'
            })
            continue

        if not csv_coordinates:
            all_results.append({
                'Patient_ID': patient_id,
                'result': 'No Data',
                'details': 'No coordinate data in CSV'
            })
            continue

        txt_coordinates = matching_txt[['index', 'key', 'x', 'y', 'z']].to_dict('records')

        # 좌표 비교
        comparison_results = compare_coordinates(csv_coordinates, txt_coordinates, location_mapping)

        # 비교 결과 저장
        for comp_result in comparison_results:
            all_results.append({
                'Patient_ID': patient_id,
                'CSV_Index': comp_result['csv_index'],
                'Location': comp_result['location'],
                'App_X': comp_result['csv_x'],
                'App_Y': comp_result['csv_y'],
                'App_Z': comp_result['csv_z'],
                'TechOps_X': comp_result['txt_x'],
                'TechOps_Y': comp_result['txt_y'],
                'TechOps_Z': comp_result['txt_z'],
                'Result': comp_result['result']
            })

        # Excel에는 있으나 CSV에 없는 index 처리
        missing_results = find_missing_in_csv(csv_coordinates, txt_coordinates, patient_id, location_mapping)
        all_results.extend(missing_results)

    # 결과 저장
    results_df = pd.DataFrame(all_results)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    output_filename = f'comparison_results_{timestamp}.xlsx'
    try:
        results_df.to_excel(output_filename, index=False)
        print(f"\n결과 파일 저장 완료: {output_filename}")
    except Exception as e:
        print(f"\n엑셀 저장 중 오류 발생: {e}")

    # 요약 통계
    if not results_df.empty and 'Result' in results_df.columns:
        print("\n=== 비교 결과 요약 ===")
        result_counts = results_df['Result'].value_counts()
        for result, count in result_counts.items():
            print(f"{result}: {count}개")
    else:
        print("\n비교 결과가 없습니다.")

    return results_df



if __name__ == "__main__":
    results = main()