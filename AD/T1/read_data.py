import pandas as pd
from io import StringIO

def read_data(csv_path, excel_path):
    try:
        with open(csv_path, 'r', encoding='ISO-8859-1') as file:
            lines = file.readlines()

        valid_lines = []
        for line in lines:
            # 여기서 특정 조건을 추가하여 문제가 있는 줄을 걸러낼 수 있습니다.
            # 예를 들어, 특정 패턴을 감지하여 제외할 수 있습니다.
            valid_lines.append(line)

        # StringIO를 사용하여 메모리에서 CSV 데이터 읽기
        csv_df = pd.read_csv(StringIO("\n".join(valid_lines)), encoding='ISO-8859-1')
        csv_df['Patient ID'] = csv_df['Patient ID'].astype(str)
        excel_df = pd.read_excel(excel_path)
        # excel_df_filtered = excel_df[['session_id', 'roi_product_name', 'Engine_raw_vol_mean', 'Engine_raw_vol_min', 'Engine_raw_vol_max']].copy()
        excel_df_filtered = excel_df[
            ['session_id', 'roi_index', 'Engine_raw_vol_mean', 'Engine_raw_vol_min', 'Engine_raw_vol_max']].copy()
        excel_df_filtered['session_id'] = excel_df_filtered['session_id'].str.lower()
        return csv_df, excel_df_filtered

    except pd.errors.ParserError as e:
        print(f"ParserError: {e}")
        raise
