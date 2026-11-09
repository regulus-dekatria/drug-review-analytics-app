"""Records: the cleaned table, one row per record, with every duplicate and quarantined row kept and marked."""
import pandas as pd
import streamlit as st

from core import DATA_DIR, is_fragment
from dash import box, empty, filters, find, hero, kpis, not_recorded, pick, show

hero("Records")
f = filters()
PATH = DATA_DIR / "records.parquet"
if not PATH.exists():
    st.info("data/records.parquet is missing. Download reviews_clean.parquet from the project Drive (derived folder) and run "
            "`python tools/make_records.py ~/Downloads/reviews_clean.parquet` once.")
    st.stop()


@st.cache_data(show_spinner="Loading the cleaned records...")
def records(mtime):
    df = pd.read_parquet(PATH)
    nr = not_recorded()
    lab = df["condition"].astype(str)
    bad = ~df["condition_valid"].astype(bool) | lab.map(is_fragment)
    df["condition_label"] = lab.where(~bad, nr)
    df["year"] = pd.to_datetime(df["review_date"]).dt.year
    return df


df = records(PATH.stat().st_mtime)
cond, med, years, ratings = f
v = df
if cond != "All conditions":
    v = v[v["condition_label"] == cond]
if med != "All medications":
    v = v[v["drugName"] == med]
v = v[v["year"].between(*years)]
if ratings:
    v = v[v["rating"].isin(ratings)]
total = len(df)
mir = int((~v["is_group_primary"]).sum())
bad = int((v["condition_label"] == not_recorded()).sum())
short = int(v["is_short_text_repeat"].sum())
show(kpis([
    ("Records in View", f"{len(v):,}", "the whole cleaned table" if len(v) == total else f"{len(v) / total * 100:.1f}% of {total:,}", "records", "database"),
    ("Distinct Reviews", f"{int(v['is_group_primary'].sum()):,}", "what every rating figure uses", "reviews", "forum"),
    ("Mirrored Copies", f"{mir:,}", "flagged, kept, never counted twice", "records", "content_copy"),
    ("No Usable Condition", f"{bad:,}", "quarantined, never guessed at", "conds", "help"),
    ("Short-Text Repeats", f"{short:,}", "flagged, too short to merge safely", "records", "short_text")], n=5))

SHOW = {"All records": None, "Mirrored copies": "mir", "No usable condition": "bad", "Short-text repeats": "short"}
SORT = {"Date, newest": ("review_date", False), "Date, oldest": ("review_date", True), "Most helpful": ("usefulCount", False),
        "Rating, highest": ("rating", False), "Rating, lowest": ("rating", True), "Medication A to Z": ("drugName", True)}
PER = 50


def tools():
    return (find("rc_q", "Search the review text"), pick("rc_show", list(SHOW), label="Show", width=180),
            pick("rc_sort", list(SORT), label="Sort", width=170))


with box("Cleaned Reviews", "rc-table", key="records", tools=tools,
         lead="One row per record. Nothing was deleted in cleaning: duplicate copies and rows without a usable condition are kept and marked.") as (q, which, sort):
    t = v
    kind = SHOW[which]
    if kind == "mir":
        t = t[~t["is_group_primary"]]
    elif kind == "bad":
        t = t[t["condition_label"] == not_recorded()]
    elif kind == "short":
        t = t[t["is_short_text_repeat"]]
    if q:
        t = t[t["review_clean"].str.contains(q, case=False, regex=False, na=False) | t["drugName"].astype(str).str.contains(q, case=False, regex=False)]
    col, asc = SORT[sort]
    t = t.sort_values(col, ascending=asc, kind="stable")
    pages = max(1, -(-len(t) // PER))
    ss = st.session_state
    key = f"rc_page_{which}_{sort}_{q}_{len(t)}"
    page = ss.get(key, 1)
    sl = t.iloc[(page - 1) * PER: page * PER]
    if len(sl):
        out = pd.DataFrame({
            "uniqueID": sl["uniqueID"].values,
            "Medication": sl["drugName"].astype(str).values,
            "Condition": [c if c != not_recorded() else ("No usable condition" if raw in ("nan", "None", "") else f"{raw} (no usable condition)")
                          for c, raw in zip(sl["condition_label"], sl["condition"].astype(str))],
            "Review": sl["review_clean"].str.slice(0, 400).values,
            "Rating": sl["rating"].values,
            "Date": pd.to_datetime(sl["review_date"]).dt.strftime("%d-%b-%Y").values,
            "Helpful": sl["usefulCount"].values,
            "Status": ["Distinct review" if p else "Mirrored copy" for p in sl["is_group_primary"]],
        })
        st.dataframe(out, hide_index=True, width="stretch", height=560, row_height=64, column_config={
            "uniqueID": st.column_config.NumberColumn(format="%d", width="small"),
            "Review": st.column_config.TextColumn(width="large"),
            "Helpful": st.column_config.NumberColumn(format="localized", width="small"),
            "Rating": st.column_config.NumberColumn(width="small")})
        with st.container(horizontal=True, vertical_alignment="center", key="ctl-pager", gap="small"):
            st.number_input("Page", 1, pages, page, key=key, width=130)
            show(f"<div class='lead-in' style='margin:0'>of {pages:,} pages · {len(t):,} records match</div>")
    else:
        show(empty("No records match."))
