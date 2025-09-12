def save_to_excel(answer_df, output_excel_file_path: str,rois):
    # 원본 스크립트처럼 스타일 없이 바로 저장
    answer_df.to_excel(output_excel_file_path)
