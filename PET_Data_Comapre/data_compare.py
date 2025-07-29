import pandas as pd
import numpy as np
from datetime import datetime


def compare_csv_files(csv1_path, csv2_path, output_path, start_column_index=13):
    """
    두 개의 CSV 파일을 비교하여 엑셀 파일로 결과를 출력하는 함수

    Parameters:
    csv1_path (str): 첫 번째 CSV 파일 경로
    csv2_path (str): 두 번째 CSV 파일 경로
    output_path (str): 출력할 엑셀 파일 경로
    start_column_index (int): 비교를 시작할 컬럼 인덱스 (기본값: 13, 즉 14번째 컬럼)
    """

    try:
        # CSV 파일 읽기
        df1 = pd.read_csv(csv1_path)
        df2 = pd.read_csv(csv2_path)

        print(f"CSV1 파일 크기: {df1.shape}")
        print(f"CSV2 파일 크기: {df2.shape}")

        # Patient ID 컬럼 확인
        patient_id_col = 'Patient ID'
        if patient_id_col not in df1.columns or patient_id_col not in df2.columns:
            raise ValueError(f"'{patient_id_col}' 컬럼이 없습니다.")

        # Patient ID로 매칭
        merged_df = pd.merge(df1, df2, on=patient_id_col, suffixes=('_CSV1', '_CSV2'))

        if merged_df.empty:
            raise ValueError("매칭되는 Patient ID가 없습니다.")

        print(f"매칭된 환자 수: {len(merged_df)}")

        # 비교할 컬럼들 확인 (start_column_index부터 마지막까지)
        # 두 CSV 파일의 컬럼을 모두 합쳐서 비교할 컬럼 리스트 생성
        df1_columns = df1.columns[start_column_index:].tolist()
        df2_columns = df2.columns[start_column_index:].tolist()

        # 두 파일의 모든 비교 컬럼을 합치고 중복 제거 (순서 유지)
        compare_columns = []
        for col in df1_columns:
            if col not in compare_columns:
                compare_columns.append(col)
        for col in df2_columns:
            if col not in compare_columns:
                compare_columns.append(col)

        print(f"CSV1 비교 컬럼 수: {len(df1_columns)}")
        print(f"CSV2 비교 컬럼 수: {len(df2_columns)}")
        print(f"전체 비교할 컬럼 수: {len(compare_columns)}")
        print(f"비교 시작 컬럼: {compare_columns[0] if compare_columns else 'None'}")
        print(f"비교 마지막 컬럼: {compare_columns[-1] if compare_columns else 'None'}")

        # 결과 데이터프레임 생성을 위한 컬럼 리스트 준비
        result_columns = [merged_df[['Patient ID']]]  # Patient ID 컬럼부터 시작

        # 각 비교 컬럼에 대해 CSV1값, CSV2값, 차이값 준비
        for col in compare_columns:
            csv1_col = f"{col}_CSV1"
            csv2_col = f"{col}_CSV2"
            diff_col = f"{col}_차이"

            # 임시 데이터프레임 생성
            temp_df = pd.DataFrame()

            # 두 파일 모두에 컬럼이 있는 경우
            if csv1_col in merged_df.columns and csv2_col in merged_df.columns:
                temp_df[f"{col}_CSV2.0.1"] = merged_df[csv1_col]
                temp_df[f"{col}_CSV2.0.2"] = merged_df[csv2_col]

                val1 = pd.to_numeric(merged_df[csv1_col], errors='coerce')
                val2 = pd.to_numeric(merged_df[csv2_col], errors='coerce')
                temp_df[diff_col] = (val1 - val2).round(7)

            # 첫 번째 파일에만 있는 경우
            elif csv1_col in merged_df.columns and csv2_col not in merged_df.columns:
                temp_df[f"{col}_CSV1"] = merged_df[csv1_col]
                temp_df[f"{col}_CSV2"] = np.nan
                temp_df[diff_col] = np.nan
                print(f"경고: {col} 컬럼이 CSV2에 없습니다.")

            # 두 번째 파일에만 있는 경우
            elif csv1_col not in merged_df.columns and csv2_col in merged_df.columns:
                temp_df[f"{col}_CSV1"] = np.nan
                temp_df[f"{col}_CSV2"] = merged_df[csv2_col]
                temp_df[diff_col] = np.nan
                print(f"경고: {col} 컬럼이 CSV1에 없습니다.")

            # 둘 다 없는 경우
            else:
                print(f"오류: {col} 컬럼을 두 파일 모두에서 찾을 수 없습니다.")
                continue

            # 컬럼 리스트에 추가
            if not temp_df.empty:
                result_columns.append(temp_df)

        # 모든 컬럼을 한번에 결합
        result_df = pd.concat(result_columns, axis=1)

        # 엑셀 파일로 저장
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            result_df.to_excel(writer, sheet_name='비교결과', index=False, float_format="%.30f")

        print(f"결과 파일이 저장되었습니다: {output_path}")

        # 통계 정보 출력
        print("\n=== 비교 통계 ===")
        diff_columns = [col for col in result_df.columns if col.endswith('_차이')]
        for col in diff_columns[:5]:  # 처음 5개 컬럼만 출력
            diff_values = result_df[col].dropna()
            if len(diff_values) > 0:
                print(f"{col.replace('_차이', '')}: 평균차이={diff_values.mean():.6f}, 최대차이={diff_values.abs().max():.6f}")

        return result_df

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return None

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# 사용 예시
if __name__ == "__main__":
    # 파일 경로 설정
    csv1_path = "CT_PET_Amyloid_SUVR_2.0.1.csv"  # 첫 번째 CSV 파일
    csv2_path = "CT_PET_Amyloid_SUVR_2.0.2.csv"  # 두 번째 CSV 파일 (실제로는 다른 파일)
    output_path = f"comparison_result_{timestamp}.xlsx"

    # 비교 실행 (14번째 컬럼부터 비교)
    result = compare_csv_files(csv1_path, csv2_path, output_path, start_column_index=13)

    if result is not None:
        print(f"\n결과 데이터프레임 크기: {result.shape}")
        print("처음 5개 컬럼 미리보기:")
        print(result.iloc[:, :5].head())