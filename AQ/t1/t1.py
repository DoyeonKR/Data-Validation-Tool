import pandas as pd
from tqdm import tqdm
import time
from mapping_dict import mapping_dict  # 딕셔너리형 매핑 테이블 불러오기

# 1. 파일 경로 설정
csv_path = "AQUAT1_이스턴.csv"
answer_path = "이스턴_t1_정답지_ZSCORE_반올림처리됨.xlsx"

# 2. 파일 불러오기
csv_df = pd.read_csv(csv_path)
answer_df = pd.read_excel(answer_path)

# 3. 정답지에서 Patient ID 추출
answer_df['Patient ID'] = answer_df['session_id'].str.extract(r'(sub_\d+)')

# 4. 매핑 딕셔너리를 이용해 display_name 매핑
answer_df['display_name'] = answer_df.apply(
    lambda row: mapping_dict.get((row['ROI'], row['roi_index']), None),
    axis=1
)

# 5. CSV에서 Patient ID 자동 추출
if 'Patient ID' not in csv_df.columns:
    if 'session_id' in csv_df.columns:
        csv_df['Patient ID'] = csv_df['session_id'].str.extract(r'(sub_\d+)')
    else:
        raise ValueError("CSV 파일에 'Patient ID' 또는 'session_id' 컬럼이 없습니다.")

# 6. 비교 함수 정의
def validate_row(row, csv_data):
    patient_id = row['Patient ID']
    column = row['display_name']
    min_val = row['Engine_raw_vol_min']
    max_val = row['Engine_raw_vol_max']

    actual_value = None

    if pd.isna(column) or column not in csv_data.columns:
        return None, 'No Match'

    patient_data = csv_data[csv_data['Patient ID'].astype(str).str.contains(patient_id)]
    if patient_data.empty:
        return None, 'No Match'

    try:
        value = float(patient_data.iloc[0][column])
        actual_value = value

        if pd.isna(value):
            return value, 'Invalid'

        # ✅ 항상 작은 쪽이 min이 되도록 처리
        lower = min(min_val, max_val)
        upper = max(min_val, max_val)

        if lower <= value <= upper:
            return value, 'PASS'
        else:
            return value, 'FAIL'

    except Exception:
        return None, 'Invalid'

# 7. 비교 수행 (진행률 표시 + 시간 측정)
print("🚀 비교 시작!")
start_time = time.time()

# tqdm + 실제값 포함 결과 수집
actuals = []
results = []

for _, row in tqdm(answer_df.iterrows(), total=len(answer_df), desc="🔍 Comparing"):
    value, result = validate_row(row, csv_df)
    actuals.append(value)
    results.append(result)

answer_df['Engine_raw_vol_actual'] = actuals
answer_df['Result'] = results


end_time = time.time()
print(f"✅ 비교 완료! 실행 시간: {end_time - start_time:.2f}초")

# 8. 결과 저장
answer_df.to_excel("AQ_T1_DataValidation.xlsx", index=False)
print("📁 결과 저장됨")