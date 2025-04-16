import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils.dataframe import dataframe_to_rows

# 1. 파일 불러오기
df_csv = pd.read_csv('SCALE MRA_Results.csv')
df_xlsx = pd.read_excel('MRA_Answer.xlsx')

# 2. 비교 대상 컬럼 정의
compare_cols = ['CoordinateX', 'CoordinateY', 'CoordinateZ', 'Maximum Diameter', 'Probability Score (RUO)']

# 3. 기준 데이터 정리
df_ref = df_xlsx[df_xlsx['roi_product_name'].isin(compare_cols)].copy()
df_ref = df_ref[['session_id', 'Aneurysm Index', 'roi_product_name', 'Engine_raw_vol_min', 'Engine_raw_vol_max']]

# 4. 결과 저장 리스트
results = []

# 5. 기준 데이터에 있는 모든 session_id + Aneurysm Index 쌍에 대해 비교 수행
unique_keys = df_ref[['session_id', 'Aneurysm Index']].drop_duplicates()

for _, key in unique_keys.iterrows():
    session_id = key['session_id']
    aneurysm_idx = key['Aneurysm Index']

    ref_group = df_ref[
        (df_ref['session_id'] == session_id) &
        (df_ref['Aneurysm Index'] == aneurysm_idx)
        ]

    match_row = df_csv[
        (df_csv['Patient ID'] == session_id) &
        (df_csv['Aneurysm Index'] == aneurysm_idx)
        ]

    if match_row.empty:
        for _, r in ref_group.iterrows():
            results.append({
                'Patient ID': session_id,
                'Aneurysm Index': aneurysm_idx,
                'Feature': r['roi_product_name'],
                'Value (CSV)': None,
                'Min (XLSX)': r['Engine_raw_vol_min'],
                'Max (XLSX)': r['Engine_raw_vol_max'],
                'Result': 'NoMatch'
            })
    else:
        row = match_row.iloc[0]
        for _, r in ref_group.iterrows():
            feature = r['roi_product_name']
            val_csv = row[feature]
            min_val = r['Engine_raw_vol_min']
            max_val = r['Engine_raw_vol_max']

            if pd.isna(min_val) or pd.isna(max_val):
                result = 'NoMatch'
            elif min_val <= val_csv <= max_val:
                result = 'Pass'
            else:
                result = 'Fail'

            results.append({
                'Patient ID': session_id,
                'Aneurysm Index': aneurysm_idx,
                'Feature': feature,
                'Value (CSV)': val_csv,
                'Min (XLSX)': min_val,
                'Max (XLSX)': max_val,
                'Result': result
            })

# 6. 결과 DataFrame 생성
df_result = pd.DataFrame(results)

# 7. 엑셀 스타일링: 색상 및 굵은 글씨
wb = Workbook()
ws = wb.active
ws.title = "비교 결과"

# 스타일 정의
fill_pass = PatternFill(start_color='CCFFCC', end_color='CCFFCC', fill_type='solid')  # 연두색
fill_fail = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')  # 핑크색
bold_font = Font(bold=True)

# 헤더 및 데이터 쓰기
for r_idx, row in enumerate(dataframe_to_rows(df_result, index=False, header=True), start=1):
    for c_idx, val in enumerate(row, start=1):
        cell = ws.cell(row=r_idx, column=c_idx, value=val)

        # 헤더 행 처리
        if r_idx == 1:
            cell.font = bold_font

        # Result 셀 처리 (7번째 열: 'Result')
        elif c_idx == len(row):  # 마지막 열이 'Result'라고 가정
            cell.font = bold_font
            if val == 'Pass':
                cell.fill = fill_pass
            elif val == 'Fail':
                cell.fill = fill_fail

# 8. 파일 저장 (중간 파일 저장 없음)
wb.save('비교결과_컬러.xlsx')
print("✅ 스타일이 적용된 최종 결과가 '비교결과_컬러.xlsx'로 저장되었습니다.")
