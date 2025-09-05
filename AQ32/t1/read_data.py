import io  # 문자열 기반 파일 객체(StringIO 등)를 사용하기 위한 표준 라이브러리
import pandas as pd  # 데이터 처리용 pandas
from AQ32.t1.mapping_dict_t1 import mapping_dict  # (ROI, roi_index) → display_name 매핑 딕셔너리


def _read_csv_robust(path: str) -> pd.DataFrame:  # 다양한 인코딩을 시도해서 CSV를 읽는 보조 함수
    """CSV 인코딩 폴백 로더 (utf-8-sig → cp949 → euc-kr → iso-8859-1 → ignore)"""
    for enc in ("utf-8-sig", "cp949", "euc-kr", "iso-8859-1"):  # 우선 시도할 인코딩 목록(순서 중요)
        try:
            return pd.read_csv(path, encoding=enc)  # 해당 인코딩으로 읽기에 성공하면 즉시 DataFrame 반환
        except Exception:
            pass  # 실패하면 다음 인코딩으로 계속 시도

    with open(path, "rb") as f:  # 모든 인코딩 시도 실패 시, 바이너리로 직접 읽어들임
        raw = f.read()  # 파일 전체 바이트 로드

    text = raw.decode("utf-8", errors="ignore")  # UTF-8로 디코딩하되, 해석 불가 문자는 무시하여 손실 복구
    return pd.read_csv(io.StringIO(text))  # 디코딩된 문자열을 파일처럼 감싸서 pandas로 재파싱


def read_data(csv_path: str, excel_path: str):  # CSV/엑셀 로드 및 전처리 수행(원본 스크립트 1~5단계 유지)
    """
    입력 파일 경로에서 DataFrame 로드 + 전처리.
    원본 스크립트의 1~5단계 로직을 유지합니다.
    반환: (csv_df, answer_df)
    """
    csv_df = _read_csv_robust(csv_path)  # 1) CSV 로드(인코딩 폴백 적용)
    answer_df = pd.read_excel(excel_path)  # 2) 엑셀(정답지) 로드

    # 3) 정답지에서 Patient ID 추출
    #  - session_id에서 (adni_숫자s숫자4자리 | sub_숫자) 패턴 추출
    if "session_id" in answer_df.columns:  # answer_df에 session_id 컬럼이 존재하는지 확인
        answer_df["Patient ID"] = answer_df["session_id"].astype(str).str.extract(  # 문자열로 변환 후 정규식 추출
            r"(adni_\d+s\d{4}|sub_\d+)"  # adni_123s0000 또는 sub_123 패턴과 매칭되는 1개 그룹을 추출
        )
    else:
        answer_df["Patient ID"] = pd.NA  # session_id가 없을 경우, 후속 로직 대비 컬럼만 생성(결측값 채움)

    # 4) 매핑 딕셔너리를 이용해 display_name 매핑
    #  - (ROI, roi_index) 튜플 키로 조회
    if {"ROI", "roi_index"} <= set(answer_df.columns):  # 두 컬럼 모두 존재하는지 검사
        answer_df["display_name"] = answer_df.apply(  # 각 행 단위로 매핑 수행
            lambda row: mapping_dict.get((row["ROI"], row["roi_index"]), None), axis=1  # (ROI, roi_index)로 매핑
        )
    else:
        answer_df["display_name"] = None  # 필요한 컬럼이 없으면 컬럼은 만들고 모든 값을 None으로 채움

    # 5) CSV에서 Patient ID 자동 추출
    if "Patient ID" not in csv_df.columns:  # CSV에 Patient ID가 없을 경우에만 자동 생성
        if "session_id" in csv_df.columns:  # 대체 키(session_id)가 있는지 확인
            csv_df["Patient ID"] = csv_df["session_id"].astype(str).str.extract(  # session_id에서 Patient ID 패턴 추출
                r"(sub_\d+)"  # CSV 측은 sub_123 형태만 추출
            )
        else:
            raise ValueError("CSV 파일에 'Patient ID' 또는 'session_id' 컬럼이 없습니다.")  # 최소 한 컬럼은 필수

    return csv_df, answer_df  # 최종 전처리 결과 반환
