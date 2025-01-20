import pandas as pd
import os

# 여러 개의 CSV 파일을 하나로 통합
def merge_csv_files(input_folder, output_file):
    # 폴더 내 모든 CSV 파일 목록 가져오기
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
    all_data = []  # 데이터를 저장할 리스트

    # CSV 파일이 없는 경우 처리
    if not csv_files:
        print(f"입력된 폴더에 CSV 파일(.csv)이 없습니다: {input_folder}")
        return

    # 모든 CSV 파일 읽어서 통합
    for file in csv_files:
        file_path = os.path.join(input_folder, file)
        try:
            df = pd.read_csv(file_path)
            all_data.append(df)
            print(f"파일 읽기 완료: {file}")
        except Exception as e:
            print(f"파일 읽기 오류: {file}, 오류: {e}")

    # 모든 데이터를 하나의 데이터프레임으로 합치기
    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)
        # 통합된 데이터 저장
        merged_df.to_csv(output_file, index=False)
        print(f"모든 파일이 통합되어 {output_file}에 저장되었습니다!")
    else:
        print("통합할 데이터가 없습니다.")

# 사용자 입력을 통한 경로 설정
if __name__ == "__main__":
    # 사용자에게 폴더 경로와 출력 파일 경로 입력받기
    input_folder = input("CSV 파일들이 있는 폴더 경로를 입력하세요: ").strip()
    output_file = input("통합된 CSV 파일을 저장할 경로와 파일명을 입력하세요 (예: merged_output.csv): ").strip()

    # 입력받은 경로로 함수 실행
    if os.path.exists(input_folder) and os.path.isdir(input_folder):
        merge_csv_files(input_folder, output_file)
    else:
        print(f"입력된 폴더 경로가 존재하지 않거나 폴더가 아닙니다: {input_folder}")
