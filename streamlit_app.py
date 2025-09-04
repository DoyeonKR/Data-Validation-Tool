import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import io, re
import matplotlib.pyplot as plt
from datetime import date

# ================== 페이지/메타 ==================
st.set_page_config(page_title="🧠 Engine Validation Summary 대시보드", layout="wide")
AUTHOR = "김도연B"
UPDATED_DATE = date.today().strftime("%Y-%m-%d")

st.title("🧠 Validation Dashboard — 멀티 파일 & 유연 컬럼 매핑")
st.caption("여러 결과 파일(엑셀/CSV) 업로드 → (자동/수동) 컬럼 매핑 → 통합 분석. "
           "중복 컬럼 자동 병합, 안전 예외 처리, 상세 결과는 좌측에 Patient ID / (있으면) Session ID 표시.")

# ================== 표준화/힌트 ==================
COLOR_MAP = {"Pass": "#8BC34A", "Fail": "#FF6F61", "NoMatch": "#B0BEC5"}
RESULT_NORMALIZE = {
    # Pass 류
    "pass": "Pass", "ok": "Pass", "true": "Pass", "success": "Pass", "matched": "Pass",
    "일치": "Pass", "정상": "Pass",
    # Fail 류
    "fail": "Fail", "ng": "Fail", "false": "Fail", "mismatch": "Fail", "error": "Fail",
    "불일치": "Fail", "실패": "Fail",
    # NoMatch/미확정 류
    "nomatch": "NoMatch", "no match": "NoMatch", "미매칭": "NoMatch", "없음": "NoMatch",
    "n/a": "NoMatch", "na": "NoMatch", "-": "NoMatch", "none": "NoMatch", "": "NoMatch",
}

# 기본 키워드
ID_HINTS = [
    "patient id","patient_id","patientid","환자","subject id","subject_id","subject",
    "case id","caseid","id"
]
RES_HINTS = [
    "overall result","result","status","outcome","compare result","validation result",
    "pass/fail","passfail","match result","검증결과","비교결과","결과","overall"
]
SESSION_HINTS = [
    "session id","session_id","sessionid","study id","study_id","series id","series_id",
    "scan id","scan_id","acquisition id","exam id","visit id","visit_id","세션","스캔","시리즈"
]

# ================== 유틸 ==================
def normalize_result(value: str) -> str:
    if value is None:
        return "NoMatch"
    s = str(value).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return RESULT_NORMALIZE.get(s, "Pass" if s == "1" else "Fail" if s == "0" else (value or "NoMatch"))

def find_column(columns, hints) -> str | None:
    """느슨한 매칭: 다국어/언더스코어/공백 차이 허용. (Index를 불리언 평가하지 않도록 방어)"""
    if columns is None:
        return None
    cols = list(columns)
    if len(cols) == 0:
        return None

    norm = [re.sub(r"[\s_]+", "", str(c).lower()) for c in cols]

    cleaned_hints = [re.sub(r"[\s_]+", "", h.lower()) for h in hints]
    for i, c in enumerate(norm):
        if any(h in c for h in cleaned_hints):
            return cols[i]

    patterns = [r"(patient|subject).*(id)$", r"(session|study|series|scan|acquisition|exam|visit).*(id)$",
                r"^(id)$", r"(overall).*result", r"^(result|status|outcome)$"]
    for pat in patterns:
        for i, c in enumerate(norm):
            if re.search(pat, c):
                return cols[i]
    return None

def merge_duplicate_named_columns(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """동일 라벨 컬럼이 2개 이상일 때 좌→우 우선으로 값 병합(bfill) 후 단일 컬럼으로 축소."""
    if df is None or name not in df.columns:
        return df
    mask = [c == name for c in df.columns]
    if sum(mask) <= 1:
        return df
    block = df.loc[:, mask]
    block = block.replace({"": pd.NA, "-": pd.NA, "NA": pd.NA, "N/A": pd.NA, "None": pd.NA, "nan": pd.NA})
    merged = block.bfill(axis=1).iloc[:, 0]
    df = df.drop(columns=[name], errors="ignore")
    df[name] = merged.fillna("-").astype(str)
    return df

def reorder_first(df: pd.DataFrame, first_cols: list[str]) -> pd.DataFrame:
    """특정 컬럼을 맨 왼쪽으로 정렬(있는 것만)."""
    cols = list(df.columns)
    left = [c for c in first_cols if c in cols]
    rest = [c for c in cols if c not in left]
    return df[left + rest]

def render_styler(styler, height=720):
    """Styler를 iframe으로 렌더해 <style> 블록 텍스트 노출 없이 스타일만 적용."""
    container_css = """
    .scrollable-table-container { max-height: 600px; overflow-y: auto; border: 1px solid #ddd; }
    .scrollable-table-container table { width: 100%; border-collapse: collapse; }
    .scrollable-table-container thead th { position: sticky; top: 0; background-color: #1919c2; color: white; z-index: 1; }
    """
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{container_css}</style></head>
<body>
<div class="scrollable-table-container">
{styler.to_html(index=False)}
</div>
</body>
</html>"""
    components.html(html, height=height, scrolling=True)

# ================== 안전한 파일 로딩 (캐시) ==================
@st.cache_data(show_spinner=False)
def read_any(uploaded_obj_bytes: bytes, filename: str, sheet_name: str | None):
    """CSV/Excel 안전 로더. 에러는 (None, err) 형태로 반환해서 UI에서 스킵."""
    try:
        name = (filename or "").lower()
        bio = io.BytesIO(uploaded_obj_bytes)
        if name.endswith(".csv"):
            df = pd.read_csv(bio, dtype=str).fillna("-")
            return df, None, "csv", None
        else:
            # Excel
            xls = pd.ExcelFile(bio)
            sheets = xls.sheet_names
            chosen = sheet_name or (sheets[0] if len(sheets) > 0 else None)
            if chosen is None:
                return None, None, "excel", f"'{filename}'에서 시트를 찾을 수 없습니다."
            df = pd.read_excel(io.BytesIO(uploaded_obj_bytes), sheet_name=chosen, dtype=str).fillna("-")
            return df, sheets, chosen, None
    except Exception as e:
        return None, None, None, f"파일 로드 오류: {e}"

# ================== 업로더 (다중) ==================
uploaded_files = st.file_uploader(
    "📥 결과 파일 업로드 (여러 개 가능, .xlsx / .csv 지원)",
    type=["xlsx", "csv"], accept_multiple_files=True
)

if not uploaded_files:
    st.info("파일을 업로드하면 자동으로 매핑/통합합니다.")
    st.stop()

# ================== 파일별 매핑 UI + 안전 스킵 ==================
st.subheader("🧩 파일별 매핑 (자동 추정 → 필요 시 수정)")
frames = []
for idx, f in enumerate(uploaded_files):
    bytes_ = f.getvalue()
    file_key = f"{idx}_{f.name}"
    is_excel = f.name.lower().endswith(".xlsx")

    with st.expander(f"📄 {f.name}", expanded=True):
        # 시트 선택(엑셀만)
        sheet_sel = None
        if is_excel:
            tmp_df, sheets, chosen, err = read_any(bytes_, f.name, None)
            if err:
                st.error(err); continue
            sheet_sel = st.selectbox("📑 시트 선택", options=list(sheets), index=0, key=f"{file_key}_sheet")

        # 실제 로드
        df, sheets, chosen, err = read_any(bytes_, f.name, sheet_sel)
        if err:
            st.error(err); continue
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            st.warning("데이터가 비어있거나 읽을 수 없습니다. 스킵합니다.")
            continue

        st.caption(f"미리보기 (상위 10행, rows={len(df)}, cols={len(df.columns)})")
        st.dataframe(df.head(10), use_container_width=True)

        # 자동 추정
        auto_id = find_column(df.columns, ID_HINTS) or (df.columns[0] if len(df.columns) > 0 else None)
        auto_res = find_column(df.columns, RES_HINTS) or (df.columns[1] if len(df.columns) > 1 else None)
        auto_sess = find_column(df.columns, SESSION_HINTS)

        if auto_id is None or auto_res is None:
            st.error("필수 컬럼을 추정할 수 없습니다. 직접 선택해 주세요.")
            auto_id = auto_id or (df.columns[0] if len(df.columns) > 0 else None)
            auto_res = auto_res or (df.columns[1] if len(df.columns) > 1 else auto_id)

        c1, c2, c3 = st.columns(3)
        with c1:
            id_col = st.selectbox(
                "환자 식별자 컬럼 (Patient ID)",
                options=list(df.columns),
                index=(list(df.columns).index(auto_id) if (auto_id in list(df.columns)) else 0),
                key=f"{file_key}_id"
            )
        with c2:
            res_col = st.selectbox(
                "결과 컬럼 (Result)",
                options=list(df.columns),
                index=(list(df.columns).index(auto_res) if (auto_res in list(df.columns)) else min(1, len(df.columns)-1)),
                key=f"{file_key}_res"
            )
        with c3:
            sess_options = ["(없음)"] + list(df.columns)
            sess_default_idx = sess_options.index(auto_sess) if (auto_sess in list(df.columns)) else 0
            sess_sel = st.selectbox("세션/스캔 식별자 (선택: Session ID 등)", options=sess_options,
                                    index=sess_default_idx, key=f"{file_key}_sess")
            sess_col = None if sess_sel == "(없음)" else sess_sel

        # 동일 컬럼 선택 방지
        chosen_set = {id_col, res_col}
        if sess_col:
            if sess_col in chosen_set:
                st.error("Session ID로 동일한 컬럼을 선택했습니다. 서로 다른 컬럼을 선택하세요.")
                continue
            chosen_set.add(sess_col)
        if id_col == res_col:
            st.error("환자 식별자 컬럼과 결과 컬럼이 동일합니다. 서로 다른 컬럼을 선택하세요.")
            continue

        norm_on = st.checkbox("결과값 정규화 (Pass/Fail/NoMatch)", value=True, key=f"{file_key}_norm")

        # 매핑
        mapped = df.copy()
        try:
            rename_map = {}
            if id_col != "Patient ID": rename_map[id_col] = "Patient ID"
            if res_col != "Result":    rename_map[res_col] = "Result"
            if sess_col and sess_col != "Session ID": rename_map[sess_col] = "Session ID"
            if rename_map:
                mapped.rename(columns=rename_map, inplace=True)
        except Exception as e:
            st.error(f"컬럼 매핑 오류: {e}"); continue

        # === 중복 컬럼 자동 병합 ===
        mapped = merge_duplicate_named_columns(mapped, "Patient ID")
        mapped = merge_duplicate_named_columns(mapped, "Result")
        if "Session ID" in mapped.columns:
            mapped = merge_duplicate_named_columns(mapped, "Session ID")

        # 필수 컬럼 확인
        if "Patient ID" not in mapped.columns or "Result" not in mapped.columns:
            st.error("필수 컬럼(환자 식별자/결과) 매핑 실패. 선택을 확인하세요.")
            continue

        # 타입/결측 정리
        mapped["Patient ID"] = mapped["Patient ID"].astype(str).fillna("-")
        mapped["Result"] = mapped["Result"].astype(str)
        if "Session ID" in mapped.columns:
            mapped["Session ID"] = mapped["Session ID"].astype(str).fillna("-")

        if norm_on:
            mapped["Result"] = mapped["Result"].apply(normalize_result)

        # 출처 메타
        mapped["Source File"] = f.name
        mapped["Source Type"] = "Excel" if is_excel else "CSV"
        mapped["Source Sheet"] = chosen if is_excel else "-"

        frames.append(mapped)

if not frames:
    st.error("통합할 유효 데이터가 없습니다.")
    st.stop()

# ================== 통합/필터 ==================
work = pd.concat(frames, ignore_index=True)

# 마지막 방어
work = merge_duplicate_named_columns(work, "Patient ID")
work = merge_duplicate_named_columns(work, "Result")
if "Session ID" in work.columns:
    work = merge_duplicate_named_columns(work, "Session ID")

work["Result"] = work["Result"].apply(normalize_result)
if "Session ID" not in work.columns:
    work["Session ID"] = "-"  # 없던 파일과의 병합 일관성

st.subheader("🎛️ 필터")
left, right = st.columns(2)
with left:
    patient_opts = ["전체"] + sorted(work["Patient ID"].astype(str).unique().tolist())
    sel_patient = st.selectbox("📌 환자 선택", patient_opts)
with right:
    result_opts = sorted(work["Result"].astype(str).unique().tolist(),
                         key=lambda x: {"Pass":0, "Fail":1, "NoMatch":2}.get(x, 99))
    sel_result = st.multiselect("🎯 결과 필터", result_opts, default=result_opts)

if sel_patient == "전체":
    filtered = work[work["Result"].isin(sel_result)].copy()
else:
    filtered = work[(work["Patient ID"] == sel_patient) & (work["Result"].isin(sel_result))].copy()

# ================== 요약/지표 ==================
st.subheader("📊 결과 요약")
summary = filtered["Result"].value_counts(dropna=False).reset_index()
summary.columns = ["결과", "건수"]
summary.index += 1

uniq_patients = filtered["Patient ID"].nunique()
st.markdown(f"**🧍 총 비교 환자 수: `{uniq_patients}명`**")
st.markdown(summary.to_html(index=True, escape=False, index_names=False, justify="left"), unsafe_allow_html=True)

total = int(summary["건수"].sum()) if len(summary) else 0
pass_count = int(summary.loc[summary["결과"] == "Pass", "건수"].sum()) if "Pass" in summary["결과"].values else 0

if total > 0:
    pass_rate = (pass_count / total) * 100
    st.metric("✅ Pass Rate", f"{pass_rate:.2f} %")
    if pass_rate < 80:
        st.error(f"⚠️ Pass Rate가 낮습니다! ({pass_rate:.2f}%)")
    elif pass_rate < 95:
        st.warning(f"주의: Pass Rate 보통 수준입니다. ({pass_rate:.2f}%)")
    else:
        st.success(f"🎉 Pass Rate 우수! ({pass_rate:.2f}%)")
else:
    st.warning("❗ 표시할 결과가 없습니다.")

# ================== 차트 ==================
st.subheader("📈 Result Distribution")
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

col1, col2 = st.columns([1, 1])

with col1:
    fig_bar, ax_bar = plt.subplots(figsize=(5, 3))
    if len(summary):
        bars = ax_bar.bar(
            summary["결과"], summary["건수"],
            width=0.4, color=[COLOR_MAP.get(r, "#CCCCCC") for r in summary["결과"]]
        )
        ax_bar.set_ylabel("Count", fontsize=11)
        ax_bar.set_title("Result Chart (Bar)", fontsize=13)
        ax_bar.grid(axis="y", linestyle="--", alpha=0.4)
        for b in bars:
            ax_bar.text(b.get_x()+b.get_width()/2, b.get_height()+0.2, f"{int(b.get_height())}",
                        ha="center", va="bottom", fontsize=10)
        if len(summary) == 1:
            ax_bar.set_xlim(-0.5, 1.5)
    st.pyplot(fig_bar)

import matplotlib.patches as mpatches
with col2:
    fig_pie, ax_pie = plt.subplots(figsize=(6, 4.5))
    if len(summary) and summary["건수"].sum() > 0:
        wedges, texts, autotexts = ax_pie.pie(
            summary["건수"], labels=None, autopct="%1.1f%%",
            startangle=90, counterclock=False,
            colors=[COLOR_MAP.get(r, "#CCCCCC") for r in summary["결과"]],
            textprops={"fontsize": 10}, pctdistance=0.7
        )
        centre = plt.Circle((0, 0), 0.5, fc="white")
        fig_pie.gca().add_artist(centre)
        ax_pie.axis("equal")
        ax_pie.set_title("Result Rate", fontsize=13)
        total_count = summary["건수"].sum()
        legend_labels = [f"{label} : {round((cnt/total_count)*100,1)}%" for label, cnt in zip(summary["결과"], summary["건수"])]
        legend_handles = [
            mpatches.Patch(color=COLOR_MAP.get(lbl, "#CCCCCC"), label=lab)
            for lbl, lab in zip(summary["결과"], legend_labels)
        ]
        ax_pie.legend(handles=legend_handles, loc="lower left", bbox_to_anchor=(-0.4, -0.15),
                      fontsize=9, frameon=False)
    else:
        ax_pie.text(0.5, 0.5, "데이터 없음", ha="center", va="center")
        ax_pie.axis("off")
    st.pyplot(fig_pie)

# ================== 상세 테이블 & 다운로드 ==================
st.subheader(f"📋 상세 비교 결과 (Total: {len(filtered)} ea)")

# 좌측에 Patient ID / Session ID가 오도록 컬럼 순서 정렬
first_cols = ["Patient ID", "Session ID"]
filtered_view = reorder_first(filtered, first_cols)

style_map = {"Pass": "#28cb2f", "Fail": "#df1010", "NoMatch": "#201b1b"}
def style_result(val):
    color = style_map.get(val, "")
    return f"background-color: {color}; color: white; font-weight: bold; text-align: center;" if color else ""

if not filtered_view.empty:
    # 'Result' 컬럼만 색상 하이라이트 (있을 때만)
    subset_cols = ["Result"] if "Result" in filtered_view.columns else []
    styled = filtered_view.style.applymap(style_result, subset=subset_cols).set_table_styles([
        {"selector": "th", "props": [("background-color", "#1919c2"), ("color", "white"),
                                     ("font-weight", "bold"), ("text-align", "center")]},
        {"selector": "td", "props": [("text-align", "center")]}
    ])
    render_styler(styled, height=720)
else:
    st.info("표시할 행이 없습니다.")

# 다운로드 (좌측 정렬된 뷰 기준)
excel_buf = io.BytesIO()
filtered_view.to_excel(excel_buf, index=False, engine="openpyxl")
excel_buf.seek(0)
suffix = "ALL" if sel_patient == "전체" else sel_patient
st.download_button(
    "📥 결과 Excel 다운로드",
    data=excel_buf,
    file_name=f"Validation_비교결과_{suffix}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
