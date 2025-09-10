
def save_to_excel(out_df, output_excel_file_path: str, rois):
    """
    원본처럼 스타일 없이 바로 저장. (원하면 색상/볼드 등 스타일링 추가 가능)
    """
    out_df.to_excel(output_excel_file_path, index=False)
