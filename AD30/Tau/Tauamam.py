import pandas as pd

# 1. 파일 경로 설정
csv_path = "Tau PET_20250610 075816.csv"
answer_path = "tau정답지.xlsx"

# 2. 파일 불러오기
csv_df = pd.read_csv(csv_path)
answer_df = pd.read_excel(answer_path)

# 3. 컬럼 정리
csv_df.columns = csv_df.columns.str.strip()
answer_df.columns = answer_df.columns.str.strip()

# 4. Patient ID 추출
answer_df['Patient ID'] = answer_df['subject'].str.extract(r'(adni_\d+s\d+|aibl_\d+|sub_\d+|irb60_\d+)')

# 5. roi_index 정수형 변환
answer_df['roi_index'] = answer_df['roi_index'].astype('Int64')

# 6. ROI 매핑
ROI_MAPPING = {
    1010: "Total Braak ROI Global SUVR",
    1110: "Left Braak ROI Global SUVR",
    1210: "Right Braak ROI Global SUVR",
    1007: "Total Braak I/II ROI SUVR",
    1107: "Left Braak I/II ROI SUVR",
    1207: "Right Braak I/II ROI SUVR",
    1001: "Total Braak I ROI SUVR",
    1101: "Left Braak I ROI SUVR",
    1201: "Right Braak I ROI SUVR",
    1002: "Total Braak II ROI SUVR",
    1102: "Left Braak II ROI SUVR",
    1202: "Right Braak II ROI SUVR",
    1008: "Total Braak III/IV ROI SUVR",
    1108: "Left Braak III/IV ROI SUVR",
    1208: "Right Braak III/IV ROI SUVR",
    1003: "Total Braak III ROI SUVR",
    1103: "Left Braak III ROI SUVR",
    1203: "Right Braak III ROI SUVR",
    1004: "Total Braak IV ROI SUVR",
    1104: "Left Braak IV ROI SUVR",
    1204: "Right Braak IV ROI SUVR",
    1009: "Total Braak V/VI ROI SUVR",
    1109: "Left Braak V/VI ROI SUVR",
    1209: "Right Braak V/VI ROI SUVR",
    1005: "Total Braak V ROI SUVR",
    1105: "Left Braak V ROI SUVR",
    1205: "Right Braak V ROI SUVR",
    1006: "Total Braak VI ROI SUVR",
    1106: "Left Braak VI ROI SUVR",
    1206: "Right Braak VI ROI SUVR",
    1020: "Total Neocortical Region SUVR",
    1120: "Left Neocortical Region SUVR",
    1220: "Right Neocortical Region SUVR",
    1021: "Total Frontal Region SUVR",
    1121: "Left Frontal Region SUVR",
    1221: "Right Frontal Region SUVR",
    1011: "Total Temporal meta ROI SUVR",
    1111: "Left Temporal meta ROI SUVR",
    1211: "Right Temporal meta ROI SUVR"
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
