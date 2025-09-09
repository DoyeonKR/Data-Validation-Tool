# import streamlit as st
# import streamlit.components.v1 as components
# import pandas as pd
# import io, re, unicodedata
# import matplotlib.pyplot as plt
# from datetime import date
#
# # ================== 페이지/메타 ==================
# st.set_page_config(page_title="🧠 Engine Validation Summary 대시보드", layout="wide")
# AUTHOR = "김도연B"
# UPDATED_DATE = date.today().strftime("%Y-%m-%d")
#
# st.title("🧠 Validation Dashboard")
# st.caption("여러 결과 파일(엑셀/CSV) 업로드 → (자동/수동) 컬럼 매핑 → 통합 분석. ")
#
# # ================== 표준화/힌트 ==================
# COLOR_MAP = {"Pass": "#8BC34A", "Fail": "#FF6F61", "NoMatch": "#B0BEC5"}
# RESULT_NORMALIZE = {
#     "pass": "Pass","ok": "Pass","true": "Pass","success": "Pass","matched": "Pass","일치": "Pass","정상": "Pass",
#     "fail": "Fail","ng": "Fail","false": "Fail","mismatch": "Fail","error": "Fail","불일치": "Fail","실패": "Fail",
#     "nomatch": "NoMatch","no match": "NoMatch","미매칭": "NoMatch","없음": "NoMatch",
#     "n/a": "NoMatch","na": "NoMatch","-": "NoMatch","none": "NoMatch","": "NoMatch",
# }
#
# ID_HINTS = ["patient id","patient_id","patientid","환자","subject id","subject_id","subject","case id","caseid","id"]
# RES_HINTS = ["overall result","result","status","outcome","compare result","validation result","pass/fail","passfail","match result","검증결과","비교결과","결과","overall"]
#
# # 세션/스캔 계열 자동 탐지 키워드
# SESSION_KEYWORDS = ["session","study","series","scan","acq","acquisition","exam","visit","세션","스캔","시리즈","스터디","방문"]
# ID_TOKENS = ["id","uid","번호","아이디","no"]
#
# # ================== 유틸 ==================
# def normalize_result(value: str) -> str:
#     if value is None:
#         return "NoMatch"
#     s = str(value).strip().lower()
#     s = re.sub(r"\s+", " ", s)
#     return RESULT_NORMALIZE.get(s, "Pass" if s == "1" else "Fail" if s == "0" else (value or "NoMatch"))
#
# def find_column(columns, hints) -> str | None:
#     if columns is None:
#         return None
#     cols = list(columns)
#     if len(cols) == 0:
#         return None
#     norm = [re.sub(r"[\s_]+", "", str(c).lower()) for c in cols]
#     cleaned_hints = [re.sub(r"[\s_]+", "", h.lower()) for h in hints]
#     for i, c in enumerate(norm):
#         if any(h in c for h in cleaned_hints):
#             return cols[i]
#     patterns = [r"(patient|subject).*(id)$", r"^(id)$", r"(overall).*result", r"^(result|status|outcome)$"]
#     for pat in patterns:
#         for i, c in enumerate(norm):
#             if re.search(pat, c):
#                 return cols[i]
#     return None
#
# def merge_duplicate_named_columns(df: pd.DataFrame, name: str) -> pd.DataFrame:
#     if df is None or name not in df.columns:
#         return df
#     mask = [c == name for c in df.columns]
#     if sum(mask) <= 1:
#         return df
#     block = df.loc[:, mask].replace({"": pd.NA, "-": pd.NA, "NA": pd.NA, "N/A": pd.NA, "None": pd.NA, "nan": pd.NA})
#     merged = block.bfill(axis=1).iloc[:, 0]
#     df = df.drop(columns=[name], errors="ignore")
#     df[name] = merged.fillna("-").astype(str)
#     return df
#
# def reorder_first(df: pd.DataFrame, first_cols: list[str]) -> pd.DataFrame:
#     cols = list(df.columns)
#     left = [c for c in first_cols if c in cols]
#     rest = [c for c in cols if c not in left]
#     return df[left + rest]
#
# def find_session_like_columns(columns):
#     cols = list(columns)
#     out = []
#     for c in cols:
#         s = str(c).strip().lower()
#         if c in ("Patient ID","Result","Session ID"):
#             continue
#         strong = any(k in s for k in SESSION_KEYWORDS) and any(t in s for t in ID_TOKENS)
#         weak = any(k in s for k in SESSION_KEYWORDS)
#         if strong or weak:
#             out.append(c)
#     uniq = []
#     seen = set()
#     for c in out:
#         if c not in seen:
#             uniq.append(c); seen.add(c)
#     return uniq
#
# def render_styler(styler, height=720):
#     """스타일 텍스트는 숨기고, 표 텍스트는 흰색으로 강제."""
#     container_css = """
#     .scrollable-table-container { max-height: 600px; overflow-y: auto; border: 1px solid #ddd; }
#     .scrollable-table-container table { width: 100%; border-collapse: collapse; color: #fff !important; }
#     .scrollable-table-container thead th { position: sticky; top: 0; background-color: #1919c2; color: #fff !important; z-index: 1; }
#     .scrollable-table-container td { color: #fff !important; }
#     """
#     html = f"""<!DOCTYPE html>
# <html>
# <head><meta charset="utf-8"><style>{container_css}</style></head>
# <body>
# <div class="scrollable-table-container">
# {styler.to_html(index=False)}
# </div>
# </body>
# </html>"""
#     components.html(html, height=height, scrolling=True)
#
# PLACEHOLDERS = {"", "-", "nan", "NaN", "NONE", "None", "N/A", "n/a"}
# def excel_like_unique_count(series: pd.Series, count_blank_as_one: bool = True) -> int:
#     s = series.copy()
#     def norm(x):
#         if pd.isna(x):
#             return None
#         y = unicodedata.normalize("NFC", str(x)).strip()
#         return None if y in PLACEHOLDERS else y
#     s = s.map(norm)
#     if count_blank_as_one:
#         s = s.fillna("__BLANK__")
#         return int(s.drop_duplicates(keep="first").shape[0])
#     else:
#         return int(s.dropna().drop_duplicates(keep="first").shape[0])
#
# # ================== 안전 로더 ==================
# @st.cache_data(show_spinner=False)
# def read_any(uploaded_obj_bytes: bytes, filename: str, sheet_name: str | None):
#     try:
#         name = (filename or "").lower()
#         bio = io.BytesIO(uploaded_obj_bytes)
#         if name.endswith(".csv"):
#             df = pd.read_csv(bio, dtype=str).fillna("-")
#             return df, None, "csv", None
#         else:
#             xls = pd.ExcelFile(bio)
#             sheets = xls.sheet_names
#             chosen = sheet_name or (sheets[0] if len(sheets) > 0 else None)
#             if chosen is None:
#                 return None, None, "excel", f"'{filename}'에서 시트를 찾을 수 없습니다."
#             df = pd.read_excel(io.BytesIO(uploaded_obj_bytes), sheet_name=chosen, dtype=str).fillna("-")
#             return df, sheets, chosen, None
#     except Exception as e:
#         return None, None, None, f"파일 로드 오류: {e}"
#
# # ================== 업로더 ==================
# uploaded_files = st.file_uploader("📥 결과 파일 업로드 (여러 개 가능, .xlsx / .csv 지원)",
#                                   type=["xlsx","csv"], accept_multiple_files=True)
# if not uploaded_files:
#     st.info("파일을 업로드하면 자동으로 매핑/통합합니다.")
#     st.stop()
#
# # ================== 파일별 매핑 ==================
# st.subheader("🧩 파일별 매핑 (자동 추정 → 필요 시 수정)")
# frames = []
# for idx, f in enumerate(uploaded_files):
#     bytes_ = f.getvalue()
#     file_key = f"{idx}_{f.name}"
#     is_excel = f.name.lower().endswith(".xlsx")
#
#     with st.expander(f"📄 {f.name}", expanded=True):
#         sheet_sel = None
#         if is_excel:
#             tmp_df, sheets, chosen, err = read_any(bytes_, f.name, None)
#             if err: st.error(err); continue
#             sheet_sel = st.selectbox("📑 시트 선택", options=list(sheets), index=0, key=f"{file_key}_sheet")
#
#         df, sheets, chosen, err = read_any(bytes_, f.name, sheet_sel)
#         if err: st.error(err); continue
#         if df is None or not isinstance(df, pd.DataFrame) or df.empty:
#             st.warning("데이터가 비어있거나 읽을 수 없습니다. 스킵합니다."); continue
#
#         st.caption(f"미리보기 (상위 10행, rows={len(df)}, cols={len(df.columns)})")
#         st.dataframe(df.head(10), use_container_width=True)
#
#         auto_id = find_column(df.columns, ID_HINTS) or (df.columns[0] if len(df.columns) > 0 else None)
#         auto_res = find_column(df.columns, RES_HINTS) or (df.columns[1] if len(df.columns) > 1 else None)
#         if auto_id is None or auto_res is None:
#             st.error("필수 컬럼을 추정할 수 없습니다. 직접 선택해 주세요.")
#             auto_id = auto_id or (df.columns[0] if len(df.columns) > 0 else None)
#             auto_res = auto_res or (df.columns[1] if len(df.columns) > 1 else auto_id)
#
#         c1, c2 = st.columns(2)
#         with c1:
#             id_col = st.selectbox("환자 식별자 컬럼 (Patient ID)", options=list(df.columns),
#                                   index=(list(df.columns).index(auto_id) if (auto_id in list(df.columns)) else 0),
#                                   key=f"{file_key}_id")
#         with c2:
#             res_col = st.selectbox("결과 컬럼 (Result)", options=list(df.columns),
#                                    index=(list(df.columns).index(auto_res) if (auto_res in list(df.columns)) else min(1, len(df.columns)-1)),
#                                    key=f"{file_key}_res")
#
#         if id_col == res_col:
#             st.error("환자 식별자와 결과 컬럼이 동일합니다. 서로 다른 컬럼을 선택하세요.")
#             continue
#
#         norm_on = st.checkbox("결과값 정규화 (Pass/Fail/NoMatch)", value=True, key=f"{file_key}_norm")
#
#         mapped = df.copy()
#         try:
#             rename_map = {}
#             if id_col != "Patient ID": rename_map[id_col] = "Patient ID"
#             if res_col != "Result":    rename_map[res_col] = "Result"
#             if rename_map: mapped.rename(columns=rename_map, inplace=True)
#         except Exception as e:
#             st.error(f"컬럼 매핑 오류: {e}"); continue
#
#         mapped = merge_duplicate_named_columns(mapped, "Patient ID")
#         mapped = merge_duplicate_named_columns(mapped, "Result")
#
#         if "Patient ID" not in mapped.columns or "Result" not in mapped.columns:
#             st.error("필수 컬럼(환자 식별자/결과) 매핑 실패. 선택을 확인하세요."); continue
#
#         mapped["Patient ID"] = mapped["Patient ID"].astype(str)
#         mapped["Result"] = mapped["Result"].astype(str)
#         if norm_on:
#             mapped["Result"] = mapped["Result"].apply(normalize_result)
#
#         mapped["Source File"]  = f.name
#         mapped["Source Type"]  = "Excel" if is_excel else "CSV"
#         mapped["Source Sheet"] = chosen if is_excel else "-"
#         frames.append(mapped)
#
# if not frames:
#     st.error("통합할 유효 데이터가 없습니다."); st.stop()
#
# # ================== 통합/필터 ==================
# work = pd.concat(frames, ignore_index=True)
# work = merge_duplicate_named_columns(work, "Patient ID")
# work = merge_duplicate_named_columns(work, "Result")
# work["Result"] = work["Result"].apply(normalize_result)
#
# st.subheader("🎛️ 필터")
# left, right = st.columns(2)
# with left:
#     # 드롭다운엔 의미 없는 빈값은 제외
#     patt_opts_series = pd.Series(work["Patient ID"])
#     patt_opts_series = patt_opts_series[~patt_opts_series.str.strip().str.lower().isin([p.lower() for p in PLACEHOLDERS])]
#     patient_opts = ["전체"] + sorted(patt_opts_series.unique().tolist())
#     sel_patient = st.selectbox("📌 환자 선택", patient_opts)
# with right:
#     result_opts = sorted(work["Result"].astype(str).unique().tolist(),
#                          key=lambda x: {"Pass":0,"Fail":1,"NoMatch":2}.get(x, 99))
#     sel_result = st.multiselect("🎯 결과 필터", result_opts, default=result_opts)
#
# if sel_patient == "전체":
#     filtered = work[work["Result"].isin(sel_result)].copy()
# else:
#     filtered = work[(work["Patient ID"] == sel_patient) & (work["Result"].isin(sel_result))].copy()
#
# # ================== 요약/지표 ==================
# st.subheader("📊 결과 요약")
#
# excel_mode = st.checkbox("엑셀 '중복값 제거' 방식으로 환자 수 계산 (빈칸 1명 포함)", value=True,
#                          help="체크 해제하면 빈칸은 제외합니다.")
# uniq_patients = excel_like_unique_count(filtered["Patient ID"], count_blank_as_one=excel_mode)
#
# summary = filtered["Result"].value_counts(dropna=False).reset_index()
# summary.columns = ["결과", "건수"]; summary.index += 1
#
# st.markdown(f"**🧍 총 비교 환자 수: `{uniq_patients}명`**")
# st.markdown(summary.to_html(index=True, escape=False, index_names=False, justify="left"), unsafe_allow_html=True)
#
# total = int(summary["건수"].sum()) if len(summary) else 0
# pass_count = int(summary.loc[summary["결과"]=="Pass","건수"].sum()) if "Pass" in summary["결과"].values else 0
#
# if total > 0:
#     pass_rate = (pass_count / total) * 100
#     st.metric("✅ Pass Rate", f"{pass_rate:.2f} %")
#     if pass_rate < 80: st.error(f"⚠️ Pass Rate가 낮습니다! ({pass_rate:.2f}%)")
#     elif pass_rate < 95: st.warning(f"주의: Pass Rate 보통 수준입니다. ({pass_rate:.2f}%)")
#     else: st.success(f"🎉 Pass Rate 우수! ({pass_rate:.2f}%)")
# else:
#     st.warning("❗ 표시할 결과가 없습니다.")
#
# # ================== 차트 ==================
# st.subheader("📈 Result Distribution")
# plt.rcParams["font.family"] = "DejaVu Sans"; plt.rcParams["axes.unicode_minus"] = False
#
# col1, col2 = st.columns([1,1])
# with col1:
#     fig_bar, ax_bar = plt.subplots(figsize=(5,3))
#     if len(summary):
#         bars = ax_bar.bar(summary["결과"], summary["건수"], width=0.4,
#                           color=[COLOR_MAP.get(r,"#CCCCCC") for r in summary["결과"]])
#         ax_bar.set_ylabel("Count", fontsize=11); ax_bar.set_title("Result Chart (Bar)", fontsize=13)
#         ax_bar.grid(axis="y", linestyle="--", alpha=0.4)
#         for b in bars:
#             ax_bar.text(b.get_x()+b.get_width()/2, b.get_height()+0.2, f"{int(b.get_height())}",
#                         ha="center", va="bottom", fontsize=10)
#         if len(summary)==1: ax_bar.set_xlim(-0.5, 1.5)
#     st.pyplot(fig_bar)
#
# import matplotlib.patches as mpatches
# with col2:
#     fig_pie, ax_pie = plt.subplots(figsize=(6,4.5))
#     if len(summary) and summary["건수"].sum() > 0:
#         wedges, texts, autotexts = ax_pie.pie(summary["건수"], labels=None, autopct="%1.1f%%",
#             startangle=90, counterclock=False,
#             colors=[COLOR_MAP.get(r,"#CCCCCC") for r in summary["결과"]],
#             textprops={"fontsize": 10}, pctdistance=0.7)
#         centre = plt.Circle((0,0), 0.5, fc="white"); fig_pie.gca().add_artist(centre)
#         ax_pie.axis("equal"); ax_pie.set_title("Result Rate", fontsize=13)
#         total_count = summary["건수"].sum()
#         legend_labels = [f"{label} : {round((cnt/total_count)*100,1)}%" for label, cnt in zip(summary["결과"], summary["건수"])]
#         legend_handles = [mpatches.Patch(color=COLOR_MAP.get(lbl,"#CCCCCC"), label=lab)
#                           for lbl, lab in zip(summary["결과"], legend_labels)]
#         ax_pie.legend(handles=legend_handles, loc="lower left", bbox_to_anchor=(-0.4, -0.15),
#                       fontsize=9, frameon=False)
#     else:
#         ax_pie.text(0.5,0.5,"데이터 없음", ha="center", va="center"); ax_pie.axis("off")
#     st.pyplot(fig_pie)
#
# # ================== 상세 테이블 & 다운로드 ==================
# st.subheader(f"📋 상세 비교 결과 (Total: {len(filtered)} ea)")
#
# # ➊ 자동 탐지된 세션/스캔 컬럼들 (원래 이름 그대로 사용)
# auto_session_cols = find_session_like_columns(filtered.columns)
#
# # ➋ 좌측 고정할 컬럼 선택 (기본: 자동 탐지 모두)
# pin_cols = st.multiselect(
#     "좌측에 고정할 세션/스캔 관련 컬럼 선택",
#     options=auto_session_cols, default=auto_session_cols,
#     help="매핑 없이도 세션/스캔/시리즈/스터디 관련 컬럼을 원래 이름 그대로 노출합니다."
# )
#
# # ➌ 좌측에 Patient ID + (선택된 세션/스캔 컬럼들) 고정
# first_cols = ["Patient ID"] + pin_cols
# display_df = filtered.copy()
# display_df["Patient ID"] = display_df["Patient ID"].fillna("-")
# filtered_view = reorder_first(display_df, first_cols)
#
# # ✅ 표시 모드 선택: 가상 스크롤(빠름, 무제한에 가까움) vs 서식강조(페이지)
# mode = st.radio(
#     "표시 모드",
#     ["빠른 전체 보기 (가상 스크롤)", "서식강조 보기 (페이지)"],
#     horizontal=True,
#     help="대용량 데이터는 '빠른 전체 보기'가 좋습니다. 색상 하이라이트가 필요하면 '서식강조'를 사용하세요."
# )
#
# style_map = {"Pass": "#28cb2f", "Fail": "#df1010", "NoMatch": "#201b1b"}
# def style_result(val):
#     color = style_map.get(val, "")
#     return f"background-color: {color}; color: white; font-weight: bold; text-align: center;" if color else ""
#
# if mode == "빠른 전체 보기 (가상 스크롤)":
#     # 가상화 표시는 색상 하이라이트가 안 되므로, 이모지로 가독성 보강
#     fast_df = filtered_view.copy()
#     if "Result" in fast_df.columns:
#         fast_df["Result"] = fast_df["Result"].map({
#             "Pass": "🟢 Pass", "Fail": "🔴 Fail", "NoMatch": "⚪ NoMatch"
#         }).fillna("-")
#     st.dataframe(fast_df, use_container_width=True, height=720)
#
# else:
#     # 서식강조 + 페이지네이션: HTML 크기를 쪼개 렌더링 한계 회피
#     total_rows = len(filtered_view)
#     page_size = st.number_input("페이지 크기 (행)", min_value=1000, max_value=50000, value=10000, step=1000,
#                                 help="페이지당 렌더링할 행 수 (Styler HTML 크기 제한 회피용)")
#     total_pages = (total_rows + page_size - 1) // page_size if total_rows else 1
#     page = st.number_input("페이지", min_value=1, max_value=max(1, total_pages), value=1, step=1)
#     start = (page - 1) * page_size
#     end = min(start + page_size, total_rows)
#     page_df = filtered_view.iloc[start:end].copy()
#
#     subset_cols = ["Result"] if "Result" in page_df.columns else []
#     styled = page_df.style.applymap(style_result, subset=subset_cols).set_table_styles([
#         {"selector": "th", "props": [("background-color", "#1919c2"), ("color", "white"),
#                                      ("font-weight", "bold"), ("text-align", "center")]},
#         {"selector": "td", "props": [("text-align", "center")]}
#     ])
#     render_styler(styled, height=720)
#     st.caption(f"{start+1:,}–{end:,} / {total_rows:,} rows")
#
# # 📥 다운로드 (좌측 정렬된 전체 뷰 기준)
# excel_buf = io.BytesIO()
# filtered_view.to_excel(excel_buf, index=False, engine="openpyxl")
# excel_buf.seek(0)
# suffix = "ALL" if sel_patient == "전체" else sel_patient
# st.download_button(
#     "📥 결과 Excel 다운로드",
#     data=excel_buf,
#     file_name=f"Validation_비교결과_{suffix}.xlsx",
#     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )
#
import os
import io
import re
import json
import time
import hashlib
import unicodedata
from datetime import date

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st
import streamlit.components.v1 as components

# ================== 페이지/메타 ==================
st.set_page_config(page_title="🧠 Engine Validation Summary 대시보드", layout="wide")
AUTHOR = "김도연B"
UPDATED_DATE = date.today().strftime("%Y-%m-%d")

st.title("🧠 Validation Dashboard")
st.caption(
    "여러 결과 파일(엑셀/CSV) 업로드 → (자동/수동) 컬럼 매핑 → 통합 분석. "
    "세션/스캔 컬럼은 매핑 없이 자동 탐지하여 좌측 고정 표시. "
    "히스토리에 누적 저장/삭제, 사용자 지정 이름 지원."
)

# ================== 히스토리 저장소 (CSV + index.json) ==================
HISTORY_DIR = "history"
INDEX_PATH = os.path.join(HISTORY_DIR, "index.json")
os.makedirs(HISTORY_DIR, exist_ok=True)


def _load_history_index():
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as f:
                idx = json.load(f)
            if isinstance(idx, list):
                return idx
        except Exception:
            pass
    return []


def _save_history_index(items):
    try:
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"히스토리 인덱스 저장 실패: {e}")


def _compute_upload_signature(uploaded_files):
    # 파일명+크기 기반 해시로 중복 저장 방지
    parts = [f"{f.name}:{len(f.getvalue())}" for f in uploaded_files]
    sig_src = "|".join(sorted(parts))
    return hashlib.sha256(sig_src.encode("utf-8")).hexdigest()


def save_history_run(df: pd.DataFrame, meta: dict) -> str:
    ts = time.strftime("%Y%m%d_%H%M%S")
    run_id = f"{ts}_{int(time.time() * 1000) % 1000:03d}"
    data_path = os.path.join(HISTORY_DIR, f"{run_id}.csv")
    meta = {**meta, "run_id": run_id, "data_path": data_path}
    try:
        df.to_csv(data_path, index=False, encoding="utf-8")
    except Exception as e:
        st.error(f"히스토리 데이터 저장 실패: {e}")
        return ""
    items = _load_history_index()
    items.append(meta)
    _save_history_index(items)
    return run_id


def list_history_items():
    items = _load_history_index()
    items.sort(key=lambda x: x.get("run_id", ""), reverse=True)
    return items


def load_history_run(run_id: str) -> pd.DataFrame | None:
    items = _load_history_index()
    for it in items:
        if it.get("run_id") == run_id:
            path = it.get("data_path")
            if path and os.path.exists(path):
                try:
                    return pd.read_csv(path, dtype=str)
                except Exception as e:
                    st.error(f"히스토리 로드 실패: {e}")
    return None


# === 히스토리 삭제 ===
def delete_history_runs(run_ids: list[str]) -> tuple[int, list[str]]:
    items = _load_history_index()
    idset = set(run_ids)
    errors = []

    # 파일 삭제
    for it in items:
        rid = it.get("run_id")
        if rid in idset:
            path = it.get("data_path")
            if path:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    errors.append(f"{rid}: 파일 삭제 실패 - {e}")

    # 인덱스 갱신
    new_items = [it for it in items if it.get("run_id") not in idset]
    removed = len(items) - len(new_items)
    _save_history_index(new_items)
    return removed, errors


# ================== 표준화/힌트 ==================
COLOR_MAP = {"Pass": "#8BC34A", "Fail": "#FF6F61", "NoMatch": "#B0BEC5"}
RESULT_NORMALIZE = {
    "pass": "Pass",
    "ok": "Pass",
    "true": "Pass",
    "success": "Pass",
    "matched": "Pass",
    "일치": "Pass",
    "정상": "Pass",
    "fail": "Fail",
    "ng": "Fail",
    "false": "Fail",
    "mismatch": "Fail",
    "error": "Fail",
    "불일치": "Fail",
    "실패": "Fail",
    "nomatch": "NoMatch",
    "no match": "NoMatch",
    "미매칭": "NoMatch",
    "없음": "NoMatch",
    "n/a": "NoMatch",
    "na": "NoMatch",
    "-": "NoMatch",
    "none": "NoMatch",
    "": "NoMatch",
}
ID_HINTS = [
    "patient id",
    "patient_id",
    "patientid",
    "환자",
    "subject id",
    "subject_id",
    "subject",
    "case id",
    "caseid",
    "id",
]
RES_HINTS = [
    "overall result",
    "result",
    "status",
    "outcome",
    "compare result",
    "validation result",
    "pass/fail",
    "passfail",
    "match result",
    "검증결과",
    "비교결과",
    "결과",
    "overall",
]
SESSION_KEYWORDS = [
    "session",
    "study",
    "series",
    "scan",
    "acq",
    "acquisition",
    "exam",
    "visit",
    "세션",
    "스캔",
    "시리즈",
    "스터디",
    "방문",
]
ID_TOKENS = ["id", "uid", "번호", "아이디", "no"]
PLACEHOLDERS = {"", "-", "nan", "NaN", "NONE", "None", "N/A", "n/a"}


# ================== 유틸 ==================
def normalize_result(value: str) -> str:
    if value is None:
        return "NoMatch"
    s = str(value).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return RESULT_NORMALIZE.get(
        s, "Pass" if s == "1" else "Fail" if s == "0" else (value or "NoMatch")
    )


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
    patterns = [
        r"(patient|subject).*(id)$",
        r"^(id)$",
        r"(overall).*result",
        r"^(result|status|outcome)$",
    ]
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
    block = df.loc[:, mask].replace(
        {
            "": pd.NA,
            "-": pd.NA,
            "NA": pd.NA,
            "N/A": pd.NA,
            "None": pd.NA,
            "nan": pd.NA,
        }
    )
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
        if c in ("Patient ID", "Result", "Session ID"):
            continue
        strong = any(k in s for k in SESSION_KEYWORDS) and any(t in s for t in ID_TOKENS)
        weak = any(k in s for k in SESSION_KEYWORDS)
        if strong or weak:
            out.append(c)
    uniq, seen = [], set()
    for c in out:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def render_styler(styler, height=720):
    """Styler를 iframe으로 렌더(텍스트로 <style> 노출 방지), 표 글자색 흰색 강제."""
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


# === 범용 추가 필터(옵션) ===
def _is_date_like(s: pd.Series) -> bool:
    try:
        sample = s.dropna().astype(str).head(200)
        if sample.empty:
            return False
        parsed = pd.to_datetime(sample, errors="coerce", utc=False)
        return parsed.notna().mean() >= 0.8
    except Exception:
        return False


def _is_numeric_like(s: pd.Series) -> bool:
    try:
        sample = s.dropna().astype(str).head(200)
        if sample.empty:
            return False
        nums = pd.to_numeric(sample, errors="coerce")
        return nums.notna().mean() >= 0.8
    except Exception:
        return False


def apply_dynamic_filters(df: pd.DataFrame, key_prefix: str = "dyn") -> pd.DataFrame:
    if df is None or df.empty:
        return df

    with st.expander("🔎 추가 필터 (모든 열)", expanded=False):
        q = st.text_input(
            "전체 빠른 검색 (부분일치, 대소문자 무시, 쉼표로 OR)",
            value="",
            key=f"{key_prefix}_quick",
        )
        use_adv = st.checkbox(
            "고급 쿼리 사용 (pandas.query)",
            value=False,
            key=f"{key_prefix}_adv_chk",
            help="예: Result == 'Fail' and `Source File`.str.contains('ARIA')",
        )
        adv = st.text_input(
            "고급 쿼리 식 (query)", value="", key=f"{key_prefix}_adv"
        ) if use_adv else ""

        cols = list(df.columns)
        num_cols, bool_cols, dt_cols = [], [], []

        # 타입 감지
        for c in cols:
            if pd.api.types.is_bool_dtype(df[c]):
                bool_cols.append(c)
                continue
            if pd.api.types.is_numeric_dtype(df[c]) or _is_numeric_like(df[c]):
                num_cols.append(c)
                continue
            if pd.api.types.is_datetime64_any_dtype(df[c]) or _is_date_like(df[c]):
                try:
                    df[c] = pd.to_datetime(df[c], errors="coerce")
                except Exception:
                    pass
                dt_cols.append(c)

        # 범주 vs 텍스트
        cat_cols, txt_cols = [], []
        for c in cols:
            if c in num_cols or c in bool_cols or c in dt_cols:
                continue
            nun = df[c].nunique(dropna=True)
            (cat_cols if nun <= 50 else txt_cols).append(c)

        # 숫자 범위
        for c in num_cols:
            s = pd.to_numeric(df[c], errors="coerce")
            if s.dropna().empty:
                continue
            lo, hi = float(np.nanmin(s)), float(np.nanmax(s))
            r = st.slider(
                f"[숫자] {c}",
                min_value=lo,
                max_value=hi,
                value=(lo, hi),
                key=f"{key_prefix}_num_{c}",
            )
            df = df[
                (pd.to_numeric(df[c], errors="coerce") >= r[0])
                & (pd.to_numeric(df[c], errors="coerce") <= r[1])
            ]

        # 날짜 범위
        for c in dt_cols:
            s = pd.to_datetime(df[c], errors="coerce")
            if s.dropna().empty:
                continue
            min_d, max_d = s.min(), s.max()
            d = st.date_input(
                f"[날짜] {c}",
                value=(min_d.date(), max_d.date()),
                key=f"{key_prefix}_dt_{c}",
            )
            if isinstance(d, tuple) and len(d) == 2:
                start = pd.to_datetime(d[0])
                end = pd.to_datetime(d[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                df = df[
                    (pd.to_datetime(df[c], errors="coerce") >= start)
                    & (pd.to_datetime(df[c], errors="coerce") <= end)
                ]

        # 불리언
        for c in bool_cols:
            opts = [True, False]
            sel = st.multiselect(
                f"[불리언] {c}", options=opts, default=opts, key=f"{key_prefix}_bool_{c}"
            )
            if len(sel) < len(opts):
                df = df[df[c].isin(sel)]

        # 범주형
        for c in cat_cols:
            uniques = df[c].dropna().astype(str).unique().tolist()
            if not uniques:
                continue
            default = st.session_state.get(f"{key_prefix}_cat_default_{c}", uniques)
            sel = st.multiselect(
                f"[범주형] {c}",
                options=uniques,
                default=default,
                key=f"{key_prefix}_cat_{c}",
            )
            st.session_state[f"{key_prefix}_cat_default_{c}"] = sel if sel else uniques
            if sel and len(sel) < len(uniques):
                df = df[df[c].astype(str).isin(sel)]

        # 텍스트 부분일치
        for c in txt_cols:
            val = st.text_input(
                f"[텍스트] {c} 포함 검색 (쉼표로 OR)", value="", key=f"{key_prefix}_txt_{c}"
            )
            if val.strip():
                tokens = [t.strip() for t in val.split(",") if t.strip()]
                if tokens:
                    pat = "|".join([re.escape(t) for t in tokens])
                    df = df[df[c].astype(str).str.contains(pat, case=False, na=False)]

        # 전체 빠른 검색
        if q.strip():
            tokens = [t.strip() for t in q.split(",") if t.strip()]
            if tokens:
                pat = "|".join([re.escape(t) for t in tokens])
                mask = df.astype(str).apply(lambda col: col.str.contains(pat, case=False, na=False))
                df = df[mask.any(axis=1)]

        # 고급 쿼리
        if use_adv and adv.strip():
            try:
                df = df.query(adv, engine="python")
            except Exception as e:
                st.warning(f"쿼리 오류: {e}")

    return df


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


# ================== 사이드바: 페이지/히스토리 컨트롤 ==================
st.sidebar.header("📄 페이지")
page = st.sidebar.radio("Go to", ["대시보드", "히스토리"], index=0, horizontal=True)

st.sidebar.header("🧾 히스토리 옵션")
auto_log = st.sidebar.checkbox("자동 기록 (업로드 변경 시 자동 저장)", value=True)
custom_label = st.sidebar.text_input("저장 이름(옵션)", placeholder="예: 2025-09-검증(ARIA-H)")
manual_save = st.sidebar.button("💾 현재 결과 수동 저장")

# ================== 대시보드 페이지 ==================
if page == "대시보드":
    uploaded_files = st.file_uploader(
        "📥 결과 파일 업로드 (여러 개 가능, .xlsx / .csv 지원)",
        type=["xlsx", "csv"],
        accept_multiple_files=True,
    )
    if not uploaded_files:
        st.info("파일을 업로드하면 자동으로 매핑/통합·분석하고, 히스토리에 누적 저장할 수 있어요.")
        st.stop()

    # ===== 파일별 매핑 =====
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
                if err:
                    st.error(err)
                    continue
                sheet_sel = st.selectbox(
                    "📑 시트 선택", options=list(sheets), index=0, key=f"{file_key}_sheet"
                )

            df, sheets, chosen, err = read_any(bytes_, f.name, sheet_sel)
            if err:
                st.error(err)
                continue
            if df is None or not isinstance(df, pd.DataFrame) or df.empty:
                st.warning("데이터가 비어있거나 읽을 수 없습니다. 스킵합니다.")
                continue

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
                id_col = st.selectbox(
                    "환자 식별자 컬럼 (Patient ID)",
                    options=list(df.columns),
                    index=(list(df.columns).index(auto_id) if (auto_id in list(df.columns)) else 0),
                    key=f"{file_key}_id",
                )
            with c2:
                res_col = st.selectbox(
                    "결과 컬럼 (Result)",
                    options=list(df.columns),
                    index=(
                        list(df.columns).index(auto_res)
                        if (auto_res in list(df.columns))
                        else min(1, len(df.columns) - 1)
                    ),
                    key=f"{file_key}_res",
                )

            if id_col == res_col:
                st.error("환자 식별자와 결과 컬럼이 동일합니다. 서로 다른 컬럼을 선택하세요.")
                continue

            norm_on = st.checkbox("결과값 정규화 (Pass/Fail/NoMatch)", value=True, key=f"{file_key}_norm")

            mapped = df.copy()
            try:
                rename_map = {}
                if id_col != "Patient ID":
                    rename_map[id_col] = "Patient ID"
                if res_col != "Result":
                    rename_map[res_col] = "Result"
                if rename_map:
                    mapped.rename(columns=rename_map, inplace=True)
            except Exception as e:
                st.error(f"컬럼 매핑 오류: {e}")
                continue

            mapped = merge_duplicate_named_columns(mapped, "Patient ID")
            mapped = merge_duplicate_named_columns(mapped, "Result")

            if "Patient ID" not in mapped.columns or "Result" not in mapped.columns:
                st.error("필수 컬럼(환자 식별자/결과) 매핑 실패. 선택을 확인하세요.")
                continue

            mapped["Patient ID"] = mapped["Patient ID"].astype(str)
            mapped["Result"] = mapped["Result"].astype(str)
            if norm_on:
                mapped["Result"] = mapped["Result"].apply(normalize_result)

            mapped["Source File"] = f.name
            mapped["Source Type"] = "Excel" if is_excel else "CSV"
            mapped["Source Sheet"] = chosen if is_excel else "-"

            frames.append(mapped)

    if not frames:
        st.error("통합할 유효 데이터가 없습니다.")
        st.stop()

    # ===== 통합/필터 =====
    work = pd.concat(frames, ignore_index=True)
    work = merge_duplicate_named_columns(work, "Patient ID")
    work = merge_duplicate_named_columns(work, "Result")
    work["Result"] = work["Result"].apply(normalize_result)

    st.subheader("🎛️ 필터")
    left, right = st.columns(2)
    with left:
        patt_opts_series = pd.Series(work["Patient ID"])
        patt_opts_series = patt_opts_series[
            ~patt_opts_series.str.strip().str.lower().isin([p.lower() for p in PLACEHOLDERS])
        ]
        patient_opts = ["전체"] + sorted(patt_opts_series.unique().tolist())
        sel_patient = st.selectbox("📌 환자 선택", patient_opts)
    with right:
        result_opts = sorted(
            work["Result"].astype(str).unique().tolist(),
            key=lambda x: {"Pass": 0, "Fail": 1, "NoMatch": 2}.get(x, 99),
        )
        sel_result = st.multiselect("🎯 결과 필터", result_opts, default=result_opts)

    if sel_patient == "전체":
        filtered = work[work["Result"].isin(sel_result)].copy()
    else:
        filtered = work[(work["Patient ID"] == sel_patient) & (work["Result"].isin(sel_result))].copy()

    # 🔎 전 컬럼 범용 필터 (옵션)
    filtered = apply_dynamic_filters(filtered, key_prefix="dyn1")

    # ===== 요약/지표 =====
    st.subheader("📊 결과 요약")
    excel_mode = st.checkbox(
        "엑셀 '중복값 제거' 방식으로 환자 수 계산 (빈칸 1명 포함)",
        value=True,
        help="체크 해제하면 빈칸은 제외합니다.",
    )
    uniq_patients = excel_like_unique_count(filtered["Patient ID"], count_blank_as_one=excel_mode)

    summary = filtered["Result"].value_counts(dropna=False).reset_index()
    summary.columns = ["결과", "건수"]
    summary.index += 1

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

    # ===== 차트 =====
    st.subheader("📈 Result Distribution")
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False

    col1, col2 = st.columns([1, 1])
    with col1:
        fig_bar, ax_bar = plt.subplots(figsize=(5, 3))
        if len(summary):
            bars = ax_bar.bar(
                summary["결과"],
                summary["건수"],
                width=0.4,
                color=[COLOR_MAP.get(r, "#CCCCCC") for r in summary["결과"]],
            )
            ax_bar.set_ylabel("Count", fontsize=11)
            ax_bar.set_title("Result Chart (Bar)", fontsize=13)
            ax_bar.grid(axis="y", linestyle="--", alpha=0.4)
            for b in bars:
                ax_bar.text(
                    b.get_x() + b.get_width() / 2,
                    b.get_height() + 0.2,
                    f"{int(b.get_height())}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                )
            if len(summary) == 1:
                ax_bar.set_xlim(-0.5, 1.5)
        st.pyplot(fig_bar)

    with col2:
        fig_pie, ax_pie = plt.subplots(figsize=(6, 4.5))
        if len(summary) and summary["건수"].sum() > 0:
            wedges, texts, autotexts = ax_pie.pie(
                summary["건수"],
                labels=None,
                autopct="%1.1f%%",
                startangle=90,
                counterclock=False,
                colors=[COLOR_MAP.get(r, "#CCCCCC") for r in summary["결과"]],
                textprops={"fontsize": 10},
                pctdistance=0.7,
            )
            centre = plt.Circle((0, 0), 0.5, fc="white")
            fig_pie.gca().add_artist(centre)
            ax_pie.axis("equal")
            ax_pie.set_title("Result Rate", fontsize=13)
            total_count = summary["건수"].sum()
            legend_labels = [
                f"{label} : {round((cnt / total_count) * 100, 1)}%"
                for label, cnt in zip(summary["결과"], summary["건수"])
            ]
            legend_handles = [
                mpatches.Patch(color=COLOR_MAP.get(lbl, "#CCCCCC"), label=lab)
                for lbl, lab in zip(summary["결과"], legend_labels)
            ]
            ax_pie.legend(
                handles=legend_handles,
                loc="lower left",
                bbox_to_anchor=(-0.4, -0.15),
                fontsize=9,
                frameon=False,
            )
        else:
            ax_pie.text(0.5, 0.5, "데이터 없음", ha="center", va="center")
            ax_pie.axis("off")
        st.pyplot(fig_pie)

    # ===== 상세 테이블 & 다운로드 =====
    st.subheader(f"📋 상세 비교 결과 (Total: {len(filtered)} ea)")

    auto_session_cols = find_session_like_columns(filtered.columns)
    pin_cols = st.multiselect(
        "좌측에 고정할 세션/스캔 관련 컬럼 선택",
        options=auto_session_cols,
        default=auto_session_cols,
        help="매핑 없이도 세션/스캔/시리즈/스터디 관련 컬럼을 원래 이름 그대로 노출합니다.",
    )

    first_cols = ["Patient ID"] + pin_cols
    display_df = filtered.copy()
    display_df["Patient ID"] = display_df["Patient ID"].fillna("-")
    filtered_view = reorder_first(display_df, first_cols)

    view_mode = st.radio("표시 모드", ["빠른 전체 보기 (가상 스크롤)", "서식강조 보기 (페이지)"], horizontal=True)

    def style_result(val):
        color = {"Pass": "#28cb2f", "Fail": "#df1010", "NoMatch": "#201b1b"}.get(val, "")
        return (
            "background-color: {c}; color: white; font-weight: bold; text-align: center;".format(c=color)
            if color
            else ""
        )

    if view_mode == "빠른 전체 보기 (가상 스크롤)":
        fast_df = filtered_view.copy()
        if "Result" in fast_df.columns:
            fast_df["Result"] = fast_df["Result"].map(
                {"Pass": "🟢 Pass", "Fail": "🔴 Fail", "NoMatch": "⚪ NoMatch"}
            ).fillna("-")
        st.dataframe(fast_df, use_container_width=True, height=720)
    else:
        total_rows = len(filtered_view)
        page_size = st.number_input("페이지 크기 (행)", min_value=1000, max_value=50000, value=10000, step=1000)
        total_pages = (total_rows + page_size - 1) // page_size if total_rows else 1
        page_no = st.number_input("페이지", min_value=1, max_value=max(1, total_pages), value=1, step=1)
        start = (page_no - 1) * page_size
        end = min(start + page_size, total_rows)
        page_df = filtered_view.iloc[start:end].copy()

        subset_cols = ["Result"] if "Result" in page_df.columns else []
        styled = (
            page_df.style.applymap(style_result, subset=subset_cols)
            .set_table_styles(
                [
                    {
                        "selector": "th",
                        "props": [
                            ("background-color", "#1919c2"),
                            ("color", "white"),
                            ("font-weight", "bold"),
                            ("text-align", "center"),
                        ],
                    },
                    {"selector": "td", "props": [("text-align", "center")]},
                ]
            )
        )
        render_styler(styled, height=720)
        st.caption(f"{start + 1:,}–{end:,} / {total_rows:,} rows")

    # 다운로드 (좌측 정렬된 전체 뷰 기준)
    excel_buf = io.BytesIO()
    filtered_view.to_excel(excel_buf, index=False, engine="openpyxl")
    excel_buf.seek(0)
    suffix = "ALL" if sel_patient == "전체" else sel_patient
    st.download_button(
        "📥 결과 Excel 다운로드",
        data=excel_buf,
        file_name=f"Validation_비교결과_{suffix}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # ===== 히스토리 저장 (자동/수동) =====
    cur_sig = _compute_upload_signature(uploaded_files)
    if "last_saved_sig" not in st.session_state:
        st.session_state["last_saved_sig"] = ""

    should_save = manual_save or (auto_log and cur_sig and st.session_state["last_saved_sig"] != cur_sig)
    if should_save:
        label_files = sorted({f.name for f in uploaded_files})
        default_label = label_files[0] + (f" 외 {len(label_files) - 1}개" if len(label_files) > 1 else "")
        label = custom_label.strip() if custom_label and custom_label.strip() else default_label

        meta = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "label": label,
            "rows": int(len(work)),
            "patients": int(excel_like_unique_count(work["Patient ID"], True)),
            "pass_rate": float((pass_count / total * 100) if total else 0),
            "files": label_files,
        }
        run_id = save_history_run(work, meta)
        if run_id:
            st.success(f"히스토리에 저장됨: {run_id} — {label}")
            # 🔧 오타 수정: 불필요한 닫는 괄호 제거
            st.session_state["last_saved_sig"] = cur_sig

# ================== 히스토리 페이지 ==================
else:
    st.header("📚 히스토리")
    items = list_history_items()
    if not items:
        st.info("아직 저장된 히스토리가 없습니다. 대시보드에서 업लोड 후 자동/수동 저장해 보세요.")
        st.stop()

    df_idx = pd.DataFrame(items)
    df_idx_view = df_idx[["run_id", "timestamp", "label", "rows", "patients", "pass_rate"]].copy()
    df_idx_view.rename(
        columns={
            "run_id": "Run ID",
            "timestamp": "Saved At",
            "label": "Label",
            "rows": "Rows",
            "patients": "Patients",
            "pass_rate": "Pass Rate(%)",
        },
        inplace=True,
    )
    st.dataframe(df_idx_view, use_container_width=True, height=300)

    # === 히스토리 삭제 UI ===
    st.subheader("🗑 히스토리 삭제")
    run_ids = df_idx["run_id"].tolist()
    del_select = st.multiselect(
        "삭제할 Run ID 선택",
        options=run_ids,
        default=[],
        help="여러 개를 선택해서 한 번에 삭제할 수 있습니다.",
    )
    col_a, col_b = st.columns([1, 2])
    with col_a:
        really = st.checkbox("정말 삭제합니다.", value=False)
    with col_b:
        if st.button("🗑 선택 삭제", disabled=(not del_select)):
            if not really:
                st.warning("삭제 확인 체크박스를 선택해 주세요.")
            else:
                removed, errs = delete_history_runs(del_select)
                if removed > 0:
                    st.success(f"{removed}개 히스토리를 삭제했습니다.")
                if errs:
                    st.warning("일부 파일 삭제 중 오류가 발생했습니다:\n- " + "\n- ".join(errs))
                st.rerun()

    st.divider()

    # === 히스토리 열람 ===
    sel_run_id = st.selectbox("🔍 열람할 Run ID 선택", options=run_ids, index=0)
    show_btn = st.button("열기")
    if show_btn and sel_run_id:
        hist_df = load_history_run(sel_run_id)
        if hist_df is None or hist_df.empty:
            st.warning("해당 히스토리 데이터가 없거나 비어 있습니다.")
        else:
            st.subheader(f"Run {sel_run_id} — 상세 보기")
            try:
                ssum = hist_df["Result"].value_counts(dropna=False).reset_index()
                ssum.columns = ["결과", "건수"]
                patients = (
                    excel_like_unique_count(hist_df["Patient ID"], True)
                    if "Patient ID" in hist_df.columns
                    else None
                )
                st.markdown(f"**Rows:** {len(hist_df):,}  |  **Patients:** {patients if patients is not None else '-'}")
                st.dataframe(ssum, use_container_width=True, height=200)
            except Exception:
                pass

            st.dataframe(hist_df, use_container_width=True, height=600)

            buf = io.BytesIO()
            hist_df.to_excel(buf, index=False, engine="openpyxl")
            buf.seek(0)
            st.download_button(
                "📥 이 히스토리 다운로드 (Excel)",
                data=buf,
                file_name=f"history_{sel_run_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
