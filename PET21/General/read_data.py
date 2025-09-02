import pandas as pd

def read_data(csv_path, excel_path):
    csv_df = pd.read_csv(csv_path)
    csv_df['Patient ID'] = csv_df['Patient ID'].astype(str)
    excel_df = pd.read_excel(excel_path)
    excel_df_filtered = excel_df[['session_id', 'roi_product_name', 'Engine_raw_vol_mean', 'Engine_raw_vol_min', 'Engine_raw_vol_max']].copy()
    excel_df_filtered['session_id'] = excel_df_filtered['session_id'].str.lower()
    return csv_df, excel_df_filtered


