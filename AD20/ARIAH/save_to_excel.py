# AD/ARIAH/save_to_excel.py
def save_to_excel(results_df, output_excel_file_path: str, rois):
    """
    process_comparison 단계 3:
    - 결과 DataFrame을 지정 경로에 저장
    - 원본 로직과 동일하게 pandas의 to_excel 사용(스타일 없음)
    """
    results_df.to_excel(output_excel_file_path, index=False)
