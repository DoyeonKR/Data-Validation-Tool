import streamlit as st
import pandas as pd
import io
import os
import matplotlib.pyplot as plt
from datetime import date

# ======== 0. 보고서 정보 변수 ========
App_VERSION = "Neurophet SCALE MRA10 1.0.0 (23.23.25172)"
Engine_VERSION = "Engine v1.0.0 (25.15.25158)"
AUTHOR = "김도연B"
UPDATED_DATE = date.today().strftime("%Y-%m-%d")

# ======== 1. 파일 체크 및 데이터 로딩 ========
if not os.path.exists("MRA_Validation.xlsx"):
    st.error("❌ 분석 결과 파일(MRA_Validation.xlsx)을 찾을 수 없습니다.")
    st.stop()

df = pd.read_excel("MRA_Validation.xlsx", dtype=str).fillna('-')

# ======== 2. 기본 페이지 설정 ========
st.set_page_config(page_title="🧠 MRA10 Validation 대시보드", layout="wide")
st.title("🧠 SCALE MRA10 Engine Validation")

# ======== 📄 보고서 정보 표시 ========
st.markdown(f"""
<small style='color: gray; font-size: 14px;'>
📄 <b>버전:</b> {App_VERSION} &nbsp;&nbsp;|&nbsp;&nbsp; ⚙️ <b>{Engine_VERSION}</b> &nbsp;&nbsp;|&nbsp;&nbsp; 🧑‍💻 <b>작성자:</b> {AUTHOR} &nbsp;&nbsp;|&nbsp;&nbsp; 📅 <b>업데이트:</b> {UPDATED_DATE}
</small>
""", unsafe_allow_html=True)

st.markdown("MRA10 Engine Data Validation 결과를 환자별, 결과별로 분석할 수 있습니다.")

# ======== 3. 필터 UI ========
patient_options = ['전체'] + sorted(df['Patient ID'].unique().tolist())
col1, col2 = st.columns(2)

with col1:
    selected_patient = st.selectbox("📌 환자 선택", patient_options)
with col2:
    selected_result = st.multiselect("🎯 결과 필터", ['Pass', 'Fail', 'NoMatch'], default=['Pass', 'Fail', 'NoMatch'])

# ======== 4. 필터링 적용 ========
if selected_patient == '전체':
    filtered_df = df[df['Result'].isin(selected_result)]
else:
    filtered_df = df[(df['Patient ID'] == selected_patient) & (df['Result'].isin(selected_result))]

# ======== 5. 결과 요약 + Pass Rate ========
st.subheader("📊 결과 요약")

summary = filtered_df['Result'].value_counts().reset_index()
summary.columns = ['결과', '건수']
summary.index += 1

# 총 데이터 수
unique_patients = filtered_df['Patient ID'].nunique()
st.markdown(f"**🧍 총 비교 환자 수: `{unique_patients}명`**")

st.markdown(
    summary.to_html(index=True, escape=False, index_names=False, justify='left'),
    unsafe_allow_html=True
)

# ✅ Pass Rate
total = summary['건수'].sum()
pass_count = summary.loc[summary['결과'] == 'Pass', '건수'].sum()

if total > 0:
    pass_rate = (pass_count / total) * 100
    st.metric(label="✅ Pass Rate", value=f"{pass_rate:.2f} %")

    if pass_rate < 80:
        st.error(f"⚠️ Pass Rate가 낮습니다! ({pass_rate:.2f}%)")
    elif pass_rate < 95:
        st.warning(f"주의: Pass Rate 보통 수준입니다. ({pass_rate:.2f}%)")
    else:
        st.success(f"🎉 Pass Rate 우수! ({pass_rate:.2f}%)")
else:
    st.warning("❗ 표시할 결과가 없습니다.")

# ======== 6. 결과 분포 차트 ========
st.subheader("📈 Result Distribution")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

color_map = {
    'Pass': '#8BC34A',
    'Fail': '#FF6F61',
    'NoMatch': '#B0BEC5'
}

col1, col2 = st.columns([1, 1])
fontsize_title = 13
fontsize_label = 11
fontsize_tick = 10

with col1:
    fig_bar, ax_bar = plt.subplots(figsize=(5, 3))
    bars = ax_bar.bar(
        summary['결과'],
        summary['건수'],
        width=0.4,  # ✅ 얇은 막대
        color=[color_map.get(r, '#CCCCCC') for r in summary['결과']]
    )
    ax_bar.set_ylabel("Count", fontsize=11)
    ax_bar.set_title("Result Chart (Bar)", fontsize=13)
    ax_bar.grid(axis='y', linestyle='--', alpha=0.4)

    # ✅ 텍스트 표시
    for bar in bars:
        yval = bar.get_height()
        ax_bar.text(bar.get_x() + bar.get_width() / 2, yval + 0.2, f'{int(yval)}',
                    ha='center', va='bottom', fontsize=10)

    # ✅ x축 범위 조정 (값이 적을 때만)
    if len(summary) == 1:
        ax_bar.set_xlim(-0.5, 1.5)

    st.pyplot(fig_bar)

with col2:
    fig_pie, ax_pie = plt.subplots(figsize=(6, 4.5))
    wedges, texts, autotexts = ax_pie.pie(
        summary['건수'],
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        counterclock=False,
        colors=[color_map.get(r, '#CCCCCC') for r in summary['결과']],
        textprops={'fontsize': fontsize_tick},
        pctdistance=0.7
    )

    # ✅ 가운데 도넛
    centre_circle = plt.Circle((0, 0), 0.5, fc='white')
    fig_pie.gca().add_artist(centre_circle)
    ax_pie.axis('equal')
    ax_pie.set_title("Result Rate", fontsize=fontsize_title)

    # ✅ 범례 텍스트를 비율로 변경
    total_count = summary['건수'].sum()
    legend_labels = [
        f"{label} : {round((count / total_count) * 100, 1)}%"
        for label, count in zip(summary['결과'], summary['건수'])
    ]
    legend_handles = [
        mpatches.Patch(color=color_map.get(label, '#CCCCCC'), label=legend)
        for label, legend in zip(summary['결과'], legend_labels)
    ]

    ax_pie.legend(
        handles=legend_handles,
        loc='lower left',
        bbox_to_anchor=(-0.4, -0.15),
        fontsize=9,
        frameon=False
    )

    st.pyplot(fig_pie)


# ======== 7. 셀 스타일 ========
style_map = {
    'Pass': '#28cb2f',
    'Fail': '#df1010',
    'NoMatch': '#201b1b'
}

def style_result(val):
    color = style_map.get(val, '')
    return f'background-color: {color}; font-weight: bold; text-align: center;' if color else ''

styled_df = filtered_df.style.applymap(style_result, subset=['Result'])\
    .set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#1919c2'), ('color', 'white'), ('font-weight', 'bold'), ('text-align', 'center')]},
        {'selector': 'td', 'props': [('text-align', 'center')]}
    ])

# ======== 8. 상세 결과 테이블 ========
st.subheader(f"📋 상세 비교 결과 (Total: {len(filtered_df)} ea)")

fixed_table_css = """
<style>
.scrollable-table-container {
    max-height: 600px;
    overflow-y: auto;
    border: 1px solid #ddd;
}

.scrollable-table-container table {
    width: 100%;
    border-collapse: collapse;
}

.scrollable-table-container thead th {
    position: sticky;
    top: 0;
    background-color: #1919c2;
    color: white;
    z-index: 1;
}
</style>
"""

table_html = styled_df.to_html(index=False)
scrollable_table_html = f"""
<div class="scrollable-table-container">
    {table_html}
</div>
"""
st.markdown(fixed_table_css + scrollable_table_html, unsafe_allow_html=True)

# ======== 9. 엑셀 다운로드 ========
excel_buffer = io.BytesIO()
filtered_df.to_excel(excel_buffer, index=False, engine='openpyxl')
excel_buffer.seek(0)

st.download_button(
    label="📥 결과 Excel 다운로드",
    data=excel_buffer,
    file_name=f"MRA_비교결과_{selected_patient}.xlsx",
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
