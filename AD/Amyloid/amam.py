import pandas as pd

# 1. 파일 경로 설정
csv_path = "Amyloid PET_20250602 090148.csv"
answer_path = "amyloid정답지.xlsx"

# 2. 파일 불러오기
csv_df = pd.read_csv(csv_path)
answer_df = pd.read_excel(answer_path)

# 3. 컬럼 정리
csv_df.columns = csv_df.columns.str.strip()
answer_df.columns = answer_df.columns.str.strip()

# 4. Patient ID 추출
answer_df['Patient ID'] = answer_df['subject'].str.extract(r'(adni_\d+s\d+|aibl_\d+|sub_\d+)')

# 5. roi_index 정수형 변환
answer_df['roi_index'] = answer_df['roi_index'].astype('Int64')

# 6. ROI 매핑
ROI_MAPPING = {
    1020: "Total Regions of Interest for Amyloid PET SUVR",
    1120: "Left Regions of Interest for Amyloid PET SUVR",
    1220: "Right Regions of Interest for Amyloid PET SUVR",
    1021: "Total Frontal Target Region SUVR",
    1121: "Left Frontal Target Region SUVR",
    1221: "Right Frontal Target Region SUVR",
    1023: "Total Lateral Parietal Target Region SUVR",
    1123: "Left Lateral Parietal Target Region SUVR",
    1223: "Right Lateral Parietal Target Region SUVR",
    39: "Total Precuneus SUVR",
    139: "Left Precuneus SUVR",
    239: "Right Precuneus SUVR",
    1022: "Total Lateral Temporal Target Region SUVR",
    1122: "Left Lateral Temporal Target Region SUVR",
    1222: "Right Lateral Temporal Target Region SUVR",
    305: "Total Cingulate Cortex SUVR",
    405: "Left Cingulate Cortex SUVR",
    505: "Right Cingulate Cortex SUVR",
    310: "Total Striatum SUVR",
    410: "Left Striatum SUVR",
    510: "Right Striatum SUVR",
}

# 7. ROI 이름 매핑
answer_df['CSV_Column'] = answer_df['roi_index'].map(ROI_MAPPING)

# 8. 유효한 ROI만 필터링
valid_df = answer_df[answer_df['CSV_Column'].notna()].copy()

# 9. 비교 함수 정의
def get_validation_result(row):
    patient_id = row['Patient ID']
    column = row['CSV_Column']
    min_val = row['guide_min (-5%)']
    max_val = row['guide_max (+5%)']

    match = csv_df[csv_df['Patient ID'] == patient_id]
    if match.empty or column not in csv_df.columns:
        return None, 'No Match'

    value = match.iloc[0][column]
    if pd.isna(value):
        return value, 'Invalid'

    return value, 'PASS' if min_val <= value <= max_val else 'FAIL'

# 10. 비교 수행
valid_df[['actual', 'result']] = valid_df.apply(
    lambda row: pd.Series(get_validation_result(row)), axis=1
)

# 11. 결과 저장
valid_df.to_excel("Amyloid_Validation_Result.xlsx", index=False)
valid_df[valid_df['result'] == 'FAIL'].to_excel("Amyloid_Validation_FailOnly.xlsx", index=False)

# 12. 통계 출력
summary = valid_df['result'].value_counts().to_frame(name='Count')
summary['Ratio (%)'] = (summary['Count'] / summary['Count'].sum() * 100).round(2)
print(summary)
