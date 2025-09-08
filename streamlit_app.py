import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import io, re, unicodedata
import matplotlib.pyplot as plt
from datetime import date

# ================== 페이지/메타 ==================
st.set_page_config(page_title="🧠 Engine Validation Summary 대시보드", layout="wide")
AUTHOR = "김도연B"
UPDATED_DATE = date.today().strftime("%Y-%m-%d")

st.title("🧠 Validation Dashboard")
st.caption("여러 결과 파일(엑셀/CSV) 업로드 → (자동/수동) 컬럼 매핑 → 통합 분석. ")

# ================== 표준화/힌트 ==================
COLOR_MAP = {"Pass": "#8BC34A", "Fail": "#FF6F61", "NoMatch": "#B0BEC5"}
RESULT_NORMALIZE = {
    "pass": "Pass","ok": "Pass","true": "Pass","success": "Pass","matched": "Pass","일치": "Pass","정상": "Pass",
    "fail": "Fail","ng": "Fail","false": "Fail","mismatch": "Fail","error": "Fail","불일치": "Fail","실패": "Fail",
    "nomatch": "NoMatch","no match": "NoMatch","미매칭": "NoMatch","없음": "NoMatch",
    "n/a": "NoMatch","na": "NoMatch","-": "NoMatch","none": "NoMatch","": "NoMatch",
}

ID_HINTS = ["patient id","patient_id","patientid","환자","subject id","subject_id","subject","case id","caseid","id"]
RES_HINTS = ["overall result","result","status","outcome","compare result","validation result","pass/fail","passfail","match result","검증결과","비교결과","결과","overall"]

# 세션/스캔 계열 자동 탐지 키워드
SESSION_KEYWORDS = ["session","study","series","scan","acq","acquisition","exam","visit","세션","스캔","시리즈","스터디","방문"]
ID_TOKENS = ["id","uid","번호","아이디","no"]

# ================== 유틸 ==================
def normalize_result(value: str) -> str:
    if value is None:
        return "NoMatch"
    s = str(value).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return RESULT_NORMALIZE.get(s, "Pass" if s == "1" else "Fail" if s == "0" else (value or "NoMatch"))

def find_column(columns, hints) -> str | None:
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
    patterns = [r"(patient|subject).*(id)$", r"^(id)$", r"(overall).*result", r"^(result|status|outcome)$"]
    for pat in patterns:
        for i, c in enumerate(norm):
            if re.search(pat, c):
                return cols[i]
    return None

def merge_duplicate_named_columns(df: pd.DataFrame, name: str) -> pd.DataFrame:
    if df is None or name not in df.columns:
        return df
    mask = [c == name for c in df.columns]
    if sum(mask) <= 1:
        return df
    block = df.loc[:, mask].replace({"": pd.NA, "-": pd.NA, "NA": pd.NA, "N/A": pd.NA, "None": pd.NA, "nan": pd.NA})
    merged = block.bfill(axis=1).iloc[:, 0]
    df = df.drop(columns=[name], errors="ignore")
    df[name] = merged.fillna("-").astype(str)
    return df

def reorder_first(df: pd.DataFrame, first_cols: list[str]) -> pd.DataFrame:
    cols = list(df.columns)
    left = [c for c in first_cols if c in cols]
    rest = [c for c in cols if c not in left]
    return df[left + rest]

def find_session_like_columns(columns):
    cols = list(columns)
    out = []
    for c in cols:
        s = str(c).strip().lower()
        if c in ("Patient ID","Result","Session ID"):
            continue
        strong = any(k in s for k in SESSION_KEYWORDS) and any(t in s for t in ID_TOKENS)
        weak = any(k in s for k in SESSION_KEYWORDS)
        if strong or weak:
            out.append(c)
    uniq = []
    seen = set()
    for c in out:
        if c not in seen:
            uniq.append(c); seen.add(c)
    return uniq

def render_styler(styler, height=720):
    """스타일 텍스트는 숨기고, 표 텍스트는 흰색으로 강제."""
    container_css = """
    .scrollable-table-container { max-height: 600px; overflow-y: auto; border: 1px solid #ddd; }
    .scrollable-table-container table { width: 100%; border-collapse: collapse; color: #fff !important; }
    .scrollable-table-container thead th { position: sticky; top: 0; background-color: #1919c2; color: #fff !important; z-index: 1; }
    .scrollable-table-container td { color: #fff !important; }
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

PLACEHOLDERS = {"", "-", "nan", "NaN", "NONE", "None", "N/A", "n/a"}
def excel_like_unique_count(series: pd.Series, count_blank_as_one: bool = True) -> int:
    s = series.copy()
    def norm(x):
        if pd.isna(x):
            return None
        y = unicodedata.normalize("NFC", str(x)).strip()
        return None if y in PLACEHOLDERS else y
    s = s.map(norm)
    if count_blank_as_one:
        s = s.fillna("__BLANK__")
        return int(s.drop_duplicates(keep="first").shape[0])
    else:
        return int(s.dropna().drop_duplicates(keep="first").shape[0])

# ================== 안전 로더 ==================
@st.cache_data(show_spinner=False)
def read_any(uploaded_obj_bytes: bytes, filename: str, sheet_name: str | None):
    try:
        name = (filename or "").lower()
        bio = io.BytesIO(uploaded_obj_bytes)
        if name.endswith(".csv"):
            df = pd.read_csv(bio, dtype=str).fillna("-")
            return df, None, "csv", None
        else:
            xls = pd.ExcelFile(bio)
            sheets = xls.sheet_names
            chosen = sheet_name or (sheets[0] if len(sheets) > 0 else None)
            if chosen is None:
                return None, None, "excel", f"'{filename}'에서 시트를 찾을 수 없습니다."
            df = pd.read_excel(io.BytesIO(uploaded_obj_bytes), sheet_name=chosen, dtype=str).fillna("-")
            return df, sheets, chosen, None
    except Exception as e:
        return None, None, None, f"파일 로드 오류: {e}"

# ================== 업로더 ==================
uploaded_files = st.file_uploader("📥 결과 파일 업로드 (여러 개 가능, .xlsx / .csv 지원)",
                                  type=["xlsx","csv"], accept_multiple_files=True)
if not uploaded_files:
    st.info("파일을 업로드하면 자동으로 매핑/통합합니다.")
    st.stop()

# ================== 파일별 매핑 ==================
st.subheader("🧩 파일별 매핑 (자동 추정 → 필요 시 수정)")
frames = []
for idx, f in enumerate(uploaded_files):
    bytes_ = f.getvalue()
    file_key = f"{idx}_{f.name}"
    is_excel = f.name.lower().endswith(".xlsx")

    with st.expander(f"📄 {f.name}", expanded=True):
        sheet_sel = None
        if is_excel:
            tmp_df, sheets, chosen, err = read_any(bytes_, f.name, None)
            if err: st.error(err); continue
            sheet_sel = st.selectbox("📑 시트 선택", options=list(sheets), index=0, key=f"{file_key}_sheet")

        df, sheets, chosen, err = read_any(bytes_, f.name, sheet_sel)
        if err: st.error(err); continue
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            st.warning("데이터가 비어있거나 읽을 수 없습니다. 스킵합니다."); continue

        st.caption(f"미리보기 (상위 10행, rows={len(df)}, cols={len(df.columns)})")
        st.dataframe(df.head(10), use_container_width=True)

        auto_id = find_column(df.columns, ID_HINTS) or (df.columns[0] if len(df.columns) > 0 else None)
        auto_res = find_column(df.columns, RES_HINTS) or (df.columns[1] if len(df.columns) > 1 else None)
        if auto_id is None or auto_res is None:
            st.error("필수 컬럼을 추정할 수 없습니다. 직접 선택해 주세요.")
            auto_id = auto_id or (df.columns[0] if len(df.columns) > 0 else None)
            auto_res = auto_res or (df.columns[1] if len(df.columns) > 1 else auto_id)

        c1, c2 = st.columns(2)
        with c1:
            id_col = st.selectbox("환자 식별자 컬럼 (Patient ID)", options=list(df.columns),
                                  index=(list(df.columns).index(auto_id) if (auto_id in list(df.columns)) else 0),
                                  key=f"{file_key}_id")
        with c2:
            res_col = st.selectbox("결과 컬럼 (Result)", options=list(df.columns),
                                   index=(list(df.columns).index(auto_res) if (auto_res in list(df.columns)) else min(1, len(df.columns)-1)),
                                   key=f"{file_key}_res")

        if id_col == res_col:
            st.error("환자 식별자와 결과 컬럼이 동일합니다. 서로 다른 컬럼을 선택하세요.")
            continue

        norm_on = st.checkbox("결과값 정규화 (Pass/Fail/NoMatch)", value=True, key=f"{file_key}_norm")

        mapped = df.copy()
        try:
            rename_map = {}
            if id_col != "Patient ID": rename_map[id_col] = "Patient ID"
            if res_col != "Result":    rename_map[res_col] = "Result"
            if rename_map: mapped.rename(columns=rename_map, inplace=True)
        except Exception as e:
            st.error(f"컬럼 매핑 오류: {e}"); continue

        mapped = merge_duplicate_named_columns(mapped, "Patient ID")
        mapped = merge_duplicate_named_columns(mapped, "Result")

        if "Patient ID" not in mapped.columns or "Result" not in mapped.columns:
            st.error("필수 컬럼(환자 식별자/결과) 매핑 실패. 선택을 확인하세요."); continue

        mapped["Patient ID"] = mapped["Patient ID"].astype(str)
        mapped["Result"] = mapped["Result"].astype(str)
        if norm_on:
            mapped["Result"] = mapped["Result"].apply(normalize_result)

        mapped["Source File"]  = f.name
        mapped["Source Type"]  = "Excel" if is_excel else "CSV"
        mapped["Source Sheet"] = chosen if is_excel else "-"
        frames.append(mapped)

if not frames:
    st.error("통합할 유효 데이터가 없습니다."); st.stop()

# ================== 통합/필터 ==================
work = pd.concat(frames, ignore_index=True)
work = merge_duplicate_named_columns(work, "Patient ID")
work = merge_duplicate_named_columns(work, "Result")
work["Result"] = work["Result"].apply(normalize_result)

st.subheader("🎛️ 필터")
left, right = st.columns(2)
with left:
    # 드롭다운엔 의미 없는 빈값은 제외
    patt_opts_series = pd.Series(work["Patient ID"])
    patt_opts_series = patt_opts_series[~patt_opts_series.str.strip().str.lower().isin([p.lower() for p in PLACEHOLDERS])]
    patient_opts = ["전체"] + sorted(patt_opts_series.unique().tolist())
    sel_patient = st.selectbox("📌 환자 선택", patient_opts)
with right:
    result_opts = sorted(work["Result"].astype(str).unique().tolist(),
                         key=lambda x: {"Pass":0,"Fail":1,"NoMatch":2}.get(x, 99))
    sel_result = st.multiselect("🎯 결과 필터", result_opts, default=result_opts)

if sel_patient == "전체":
    filtered = work[work["Result"].isin(sel_result)].copy()
else:
    filtered = work[(work["Patient ID"] == sel_patient) & (work["Result"].isin(sel_result))].copy()

# ================== 요약/지표 ==================
st.subheader("📊 결과 요약")

excel_mode = st.checkbox("엑셀 '중복값 제거' 방식으로 환자 수 계산 (빈칸 1명 포함)", value=True,
                         help="체크 해제하면 빈칸은 제외합니다.")
uniq_patients = excel_like_unique_count(filtered["Patient ID"], count_blank_as_one=excel_mode)

summary = filtered["Result"].value_counts(dropna=False).reset_index()
summary.columns = ["결과", "건수"]; summary.index += 1

st.markdown(f"**🧍 총 비교 환자 수: `{uniq_patients}명`**")
st.markdown(summary.to_html(index=True, escape=False, index_names=False, justify="left"), unsafe_allow_html=True)

total = int(summary["건수"].sum()) if len(summary) else 0
pass_count = int(summary.loc[summary["결과"]=="Pass","건수"].sum()) if "Pass" in summary["결과"].values else 0

if total > 0:
    pass_rate = (pass_count / total) * 100
    st.metric("✅ Pass Rate", f"{pass_rate:.2f} %")
    if pass_rate < 80: st.error(f"⚠️ Pass Rate가 낮습니다! ({pass_rate:.2f}%)")
    elif pass_rate < 95: st.warning(f"주의: Pass Rate 보통 수준입니다. ({pass_rate:.2f}%)")
    else: st.success(f"🎉 Pass Rate 우수! ({pass_rate:.2f}%)")
else:
    st.warning("❗ 표시할 결과가 없습니다.")

# ================== 차트 ==================
st.subheader("📈 Result Distribution")
plt.rcParams["font.family"] = "DejaVu Sans"; plt.rcParams["axes.unicode_minus"] = False

col1, col2 = st.columns([1,1])
with col1:
    fig_bar, ax_bar = plt.subplots(figsize=(5,3))
    if len(summary):
        bars = ax_bar.bar(summary["결과"], summary["건수"], width=0.4,
                          color=[COLOR_MAP.get(r,"#CCCCCC") for r in summary["결과"]])
        ax_bar.set_ylabel("Count", fontsize=11); ax_bar.set_title("Result Chart (Bar)", fontsize=13)
        ax_bar.grid(axis="y", linestyle="--", alpha=0.4)
        for b in bars:
            ax_bar.text(b.get_x()+b.get_width()/2, b.get_height()+0.2, f"{int(b.get_height())}",
                        ha="center", va="bottom", fontsize=10)
        if len(summary)==1: ax_bar.set_xlim(-0.5, 1.5)
    st.pyplot(fig_bar)

import matplotlib.patches as mpatches
with col2:
    fig_pie, ax_pie = plt.subplots(figsize=(6,4.5))
    if len(summary) and summary["건수"].sum() > 0:
        wedges, texts, autotexts = ax_pie.pie(summary["건수"], labels=None, autopct="%1.1f%%",
            startangle=90, counterclock=False,
            colors=[COLOR_MAP.get(r,"#CCCCCC") for r in summary["결과"]],
            textprops={"fontsize": 10}, pctdistance=0.7)
        centre = plt.Circle((0,0), 0.5, fc="white"); fig_pie.gca().add_artist(centre)
        ax_pie.axis("equal"); ax_pie.set_title("Result Rate", fontsize=13)
        total_count = summary["건수"].sum()
        legend_labels = [f"{label} : {round((cnt/total_count)*100,1)}%" for label, cnt in zip(summary["결과"], summary["건수"])]
        legend_handles = [mpatches.Patch(color=COLOR_MAP.get(lbl,"#CCCCCC"), label=lab)
                          for lbl, lab in zip(summary["결과"], legend_labels)]
        ax_pie.legend(handles=legend_handles, loc="lower left", bbox_to_anchor=(-0.4, -0.15),
                      fontsize=9, frameon=False)
    else:
        ax_pie.text(0.5,0.5,"데이터 없음", ha="center", va="center"); ax_pie.axis("off")
    st.pyplot(fig_pie)

# ================== 상세 테이블 & 다운로드 ==================
st.subheader(f"📋 상세 비교 결과 (Total: {len(filtered)} ea)")

# ➊ 자동 탐지된 세션/스캔 컬럼들 (원래 이름 그대로 사용)
auto_session_cols = find_session_like_columns(filtered.columns)

# ➋ 좌측 고정할 컬럼 선택 (기본: 자동 탐지 모두)
pin_cols = st.multiselect(
    "좌측에 고정할 세션/스캔 관련 컬럼 선택",
    options=auto_session_cols, default=auto_session_cols,
    help="매핑 없이도 세션/스캔/시리즈/스터디 관련 컬럼을 원래 이름 그대로 노출합니다."
)

# ➌ 좌측에 Patient ID + (선택된 세션/스캔 컬럼들) 고정
first_cols = ["Patient ID"] + pin_cols
display_df = filtered.copy()
display_df["Patient ID"] = display_df["Patient ID"].fillna("-")
filtered_view = reorder_first(display_df, first_cols)

# ✅ 표시 모드 선택: 가상 스크롤(빠름, 무제한에 가까움) vs 서식강조(페이지)
mode = st.radio(
    "표시 모드",
    ["빠른 전체 보기 (가상 스크롤)", "서식강조 보기 (페이지)"],
    horizontal=True,
    help="대용량 데이터는 '빠른 전체 보기'가 좋습니다. 색상 하이라이트가 필요하면 '서식강조'를 사용하세요."
)

style_map = {"Pass": "#28cb2f", "Fail": "#df1010", "NoMatch": "#201b1b"}
def style_result(val):
    color = style_map.get(val, "")
    return f"background-color: {color}; color: white; font-weight: bold; text-align: center;" if color else ""

if mode == "빠른 전체 보기 (가상 스크롤)":
    # 가상화 표시는 색상 하이라이트가 안 되므로, 이모지로 가독성 보강
    fast_df = filtered_view.copy()
    if "Result" in fast_df.columns:
        fast_df["Result"] = fast_df["Result"].map({
            "Pass": "🟢 Pass", "Fail": "🔴 Fail", "NoMatch": "⚪ NoMatch"
        }).fillna("-")
    st.dataframe(fast_df, use_container_width=True, height=720)

else:
    # 서식강조 + 페이지네이션: HTML 크기를 쪼개 렌더링 한계 회피
    total_rows = len(filtered_view)
    page_size = st.number_input("페이지 크기 (행)", min_value=1000, max_value=50000, value=10000, step=1000,
                                help="페이지당 렌더링할 행 수 (Styler HTML 크기 제한 회피용)")
    total_pages = (total_rows + page_size - 1) // page_size if total_rows else 1
    page = st.number_input("페이지", min_value=1, max_value=max(1, total_pages), value=1, step=1)
    start = (page - 1) * page_size
    end = min(start + page_size, total_rows)
    page_df = filtered_view.iloc[start:end].copy()

    subset_cols = ["Result"] if "Result" in page_df.columns else []
    styled = page_df.style.applymap(style_result, subset=subset_cols).set_table_styles([
        {"selector": "th", "props": [("background-color", "#1919c2"), ("color", "white"),
                                     ("font-weight", "bold"), ("text-align", "center")]},
        {"selector": "td", "props": [("text-align", "center")]}
    ])
    render_styler(styled, height=720)
    st.caption(f"{start+1:,}–{end:,} / {total_rows:,} rows")

# 📥 다운로드 (좌측 정렬된 전체 뷰 기준)
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

