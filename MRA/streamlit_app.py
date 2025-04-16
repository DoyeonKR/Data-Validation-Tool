import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

# 1. 데이터 불러오기
df = pd.read_excel("비교결과_컬러.xlsx")

# 2. 데이터 타입 변환 (에러 방지)
df['Value (CSV)'] = df['Value (CSV)'].astype(str)
df['Min (XLSX)'] = df['Min (XLSX)'].astype(str)
df['Max (XLSX)'] = df['Max (XLSX)'].astype(str)

# 3. 페이지 기본 설정
st.set_page_config(page_title="MRA 전체 대시보드", layout="wide")
st.title("🧠 SCALE MRA Engine Validation")
st.markdown("MRA Validation 결과를 환자별, 결과별로 분석할 수 있습니다.")

# 4. 필터 UI
patient_options = ['전체'] + sorted(df['Patient ID'].unique().tolist())
col1, col2 = st.columns(2)

with col1:
    selected_patient = st.selectbox("📌 환자 선택", patient_options)
with col2:
    selected_result = st.multiselect("🎯 결과 필터", ['Pass', 'Fail', 'NoMatch'], default=['Pass', 'Fail', 'NoMatch'])

# 5. 필터링
if selected_patient == '전체':
    filtered_df = df[df['Result'].isin(selected_result)]
else:
    filtered_df = df[(df['Patient ID'] == selected_patient) & (df['Result'].isin(selected_result))]

# 6. 결과 요약 표
st.subheader("📊 결과 요약")
summary = filtered_df['Result'].value_counts().reset_index()
summary.columns = ['결과', '건수']
st.table(summary)

# # 7. 요약 차트 시각화
# st.subheader("📈 결과 분포 차트")
# fig, ax = plt.subplots()
# ax.bar(summary['Result'], summary['Quantity'], color=['#CCFFCC' if r == 'Pass' else '#FFCCCC' if r == 'Fail' else '#201b1b' for r in summary['Result']])
# ax.set_ylabel("Quantity")
# ax.set_xlabel("Result")
# ax.set_title("Summary")
# st.pyplot(fig)

# 8. 셀 색상 스타일링 함수
def style_result(val):
    if val == 'Pass':
        return 'background-color: #28cb2f; font-weight: bold; text-align: center;'
    elif val == 'Fail':
        return 'background-color: #df1010; font-weight: bold; text-align: center;'
    elif val == 'NoMatch':
        return 'background-color: #201b1b; font-weight: bold; text-align: center;'
    return ''

styled_df = filtered_df.style.applymap(style_result, subset=['Result'])\
    .set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#1919c2'), ('font-weight', 'bold'), ('text-align', 'center')]},
        {'selector': 'td', 'props': [('text-align', 'center')]}
    ])

# 9. 스타일링된 테이블 출력
st.subheader("📋 상세 비교 결과")
st.markdown(styled_df.to_html(index=False), unsafe_allow_html=True)

# 10. 엑셀 다운로드
excel_buffer = io.BytesIO()
filtered_df.to_excel(excel_buffer, index=False, engine='openpyxl')
excel_buffer.seek(0)

st.download_button(
    label="📥 필터링된 결과 Excel 다운로드",
    data=excel_buffer,
    file_name=f"MRA_비교결과_{selected_patient}.xlsx",
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
