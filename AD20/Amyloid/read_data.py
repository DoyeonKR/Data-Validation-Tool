import pandas as pd

def read_data(csv_path, excel_path):
    #CSV 파일을 읽어서 DataFrame으로 로드
    csv_df = pd.read_csv(csv_path)
    # 'Patient ID' 컬럼의 자료형을 문자열(str)로 변환
    # → 숫자형 ID도 문자열로 맞춰서 비교 시 타입 불일치 방지
    csv_df['Patient ID'] = csv_df['Patient ID'].astype(str)
    # Excel 파일을 읽어서 DataFrame으로 로드
    excel_df = pd.read_excel(excel_path)
    # 필요한 컬럼만 선택하여 새로운 DataFrame 생성
    # 'session_id', 'roi_product_name', 'Engine_raw_vol_mean',
    # 'Engine_raw_vol_min', 'Engine_raw_vol_max'
    excel_df_filtered = excel_df[['session_id', 'roi_product_name', 'Engine_raw_vol_mean', 'Engine_raw_vol_min', 'Engine_raw_vol_max']].copy()
    # 'session_id' 컬럼의 값을 전부 소문자로 변환
    # → 대소문자 차이로 인한 매칭 오류 방지
    excel_df_filtered['session_id'] = excel_df_filtered['session_id'].str.lower()
    # 두 개의 DataFrame을 반환
    return csv_df, excel_df_filtered