import pandas as pd

# 파일 경로 설정
excel_path = "SWI.xlsx"  # ← 여기에 실제 엑셀 정답지 경로 입력
csv_path = "ARIA-H_20250609 044740.csv"  # CSV 파일 경로

# 데이터 로드
excel_df = pd.read_excel(excel_path)
csv_df = pd.read_csv(csv_path, encoding='cp949')  # 인코딩은 상황에 맞게 cp949 또는 utf-8

# ID 정규화 함수
def normalize_id(value):
    return str(value).strip().lower().replace('_', '').replace('-', '')

# 정규화된 ID 컬럼 생성
excel_df['Normalized_ID'] = excel_df['session_id'].apply(normalize_id)
csv_df['Normalized_ID'] = csv_df['Patient ID'].apply(normalize_id)

# 비교 결과 리스트
results = []

for _, row in excel_df.iterrows():
    session_id = row['session_id']
    true_val = row['Total Microhemorrhage Count']
    norm_id = row['Normalized_ID']

    match_row = csv_df[csv_df['Normalized_ID'] == norm_id]

    if match_row.empty:
        result = {
            'Session ID': session_id,
            'Patient ID': 'No Match',
            'True Value': true_val,
            'Predicted Value': 'None',
            'Result': 'No Match'
        }
    else:
        pred_val = match_row.iloc[0]['Total Microhemorrhage Count']
        try:
            result_flag = 'PASS' if int(pred_val) == int(true_val) else 'FAIL'
        except:
            result_flag = 'Invalid'

        result = {
            'Session ID': session_id,
            'Patient ID': match_row.iloc[0]['Patient ID'],
            'True Value': true_val,
            'Predicted Value': pred_val,
            'Result': result_flag
        }

    results.append(result)

# 결과 저장
results_df = pd.DataFrame(results)
results_df.to_excel("SWI_TotalMicrohemorrhage_비교결과.xlsx", index=False)
