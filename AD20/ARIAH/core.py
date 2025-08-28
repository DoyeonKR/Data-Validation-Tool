# AD/ARIAH/core.py
import pandas as pd
import re
from datetime import datetime

def load_and_prepare_data():
    """데이터 파일들을 로드하고 전처리"""

    # CSV 파일 읽기
    try:
        csv_data = pd.read_csv('ARIA-H (Microhemorrhage)_2025-08-05.csv')
        print(f"CSV 파일 로드 완료: {len(csv_data)} 행")
    except Exception as e:
        print(f"CSV 파일 로드 오류: {e}")
        return None, None

    try:
        excel_data = pd.read_excel('250731_ARIA_H_v122.xlsx')
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
    """원본 스크립트의 메인. (서버에서는 어댑터를 통해 함수들만 호출)"""
    print("=== CSV vs Excel ARIA H 파일 비교 도구 ===\n")
    csv_data, txt_data = load_and_prepare_data()
    if csv_data is None or txt_data is None:
        return
    # 이하 로직은 서버 어댑터에서 동일하게 수행하므로 생략
    # ...
    return
