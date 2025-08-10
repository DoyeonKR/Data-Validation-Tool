import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- 함수 정의 ---

def clean_and_analyze(df, label):
    df_cleaned = df.copy()
    df_cleaned['Result'] = df_cleaned['Result'].str.upper().str.strip()
    df_filtered = df_cleaned[df_cleaned['Result'].isin(['PASS', 'FAIL'])]

    result_counts = df_filtered['Result'].value_counts()
    total = result_counts.sum()
    pass_count = result_counts.get('PASS', 0)
    fail_count = result_counts.get('FAIL', 0)
    pass_ratio = round(pass_count / total * 100, 2) if total else 0
    fail_ratio = round(fail_count / total * 100, 2) if total else 0

    summary = {
        "총 검사 수": total,
        "PASS 수": pass_count,
        "FAIL 수": fail_count,
        "PASS 비율 (%)": pass_ratio,
        "FAIL 비율 (%)": fail_ratio,
    }

    return df_filtered, summary, result_counts


def draw_bar_chart(counts, label):
    fig, ax = plt.subplots()
    counts = counts.reindex(['PASS', 'FAIL'])  # 고정 순서
    ax.bar(counts.index, counts.values)
    ax.set_title(f"{label} PASS / FAIL 분포")
    ax.set_ylabel("개수")
    ax.set_xlabel("결과")
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    return fig

# --- 파일 업로드 ---
st.title("🔍 PASS / FAIL 데이터 검증 대시보드")

uploaded_files = st.file_uploader(
    "엑셀 파일 3개를 업로드 해주세요",
    type=["xlsx"],
    accept_multiple_files=True
)

if uploaded_files and len(uploaded_files) == 3:
    tabs = st.tabs(["📁 " + file.name for file in uploaded_files])

    for i, file in enumerate(uploaded_files):
        with tabs[i]:
            df = pd.read_excel(file)
            label = file.name.split('.')[0]

            filtered_df, summary, result_counts = clean_and_analyze(df, label)

            # 요약 정보 출력
            st.subheader("📊 결과 요약")
            st.dataframe(pd.DataFrame([summary]))

            # 막대 그래프
            st.subheader("📈 PASS / FAIL 막대 그래프")
            st.pyplot(draw_bar_chart(result_counts, label))


else:
    st.info("⚠️ 엑셀 파일을 업로드 해주세요")
