"""Predictive Insights: where the models would send the pharmacy team, on reviews they never saw."""
import streamlit as st

from core import metrics, predictive_cube
from dash import bars, box, empty, esc, filters, find, hero, kpis, legend, not_recorded, note, pair, pct, pick, show, table

hero("Predictive Insights")
cond, med, _, _ = filters(show_years=False, show_ratings=False)
pc = predictive_cube()
if pc is None:
    st.error("data/predictive_cube.parquet is missing.")
    st.stop()
v = pc
if cond != "All conditions":
    v = v[v["condition_label"] == cond]
if med != "All medications":
    v = v[v["drugName"] == med]
n = int(v["test_reviews"].sum())
if not n:
    st.warning("No 2016 or 2017 reviews match these filters.")
    st.stop()

m = metrics() or {}
cap = (m.get("objective1", {}).get("capture_rate") or {}).get("20%")
st.markdown(kpis([
    ("Reviews Checked", f"{n:,}", "posted 2016 to 2017, unseen by the model", "test_reviews", "fact_check"),
    ("Actually Rated Low", pct(v["actual_low"].sum() / n), "patients who gave 1 to 3", "recall_low", "sentiment_dissatisfied"),
    ("Flagged Low", pct(v["pred_low"].sum() / n), "flagged from the review text alone", "severe", "flag"),
    ("Low Found in the Top 20%", pct(cap) if cap else "-", "of poor experiences, reading a fifth of the inbox", "capture", "manage_search")]),
    unsafe_allow_html=True)

nr = not_recorded()
by = "condition_label" if cond == "All conditions" else "drugName"
cols = ["test_reviews", "actual_low", "pred_low", "actual_high", "pred_high", "p_low_sum", "helpful_actual", "helpful_score_sum"]
g_all = v[v["condition_label"] != nr].groupby(by)[cols].sum().sort_values("test_reviews", ascending=False)
g_all = g_all.assign(actual=g_all["actual_low"] / g_all["test_reviews"], called=g_all["pred_low"] / g_all["test_reviews"],
                     chance=g_all["p_low_sum"] / g_all["test_reviews"], helpful=g_all["helpful_actual"] / g_all["test_reviews"],
                     helpful_pred=g_all["helpful_score_sum"] / g_all["test_reviews"])
g_all["gap"] = (g_all["called"] - g_all["actual"]).abs()
what = "conditions" if by == "condition_label" else f"medications for {cond}"
noun = "Conditions" if by == "condition_label" else "Medications"
one = noun[:-1].lower()
PMINS = [100, 30, 1] if by == "condition_label" else [20, 10, 1]
pmin_fmt = lambda x: "Any number" if x == 1 else f"{x}+ reviews"

top = g_all[g_all["test_reviews"] >= PMINS[0]].head(10)
pairs = "".join(
    f"<div class='bar pair' style='--lw:180px;--pw:120px' data-tip='{esc(k)}&#10;actually Low: {r.actual * 100:.1f}%&#10;flagged Low: {r.called * 100:.1f}%&#10;{int(r.test_reviews):,} reviews'>"
    f"<span class='name'>{esc(k)}</span><div style='flex:1'>"
    f"<div class='track' style='margin-bottom:3px'><div class='fill lead' style='width:{r.actual * 100:.1f}%;--d:{.15 + i * .04:.2f}s'></div></div>"
    f"<div class='track'><div class='fill b' style='width:{r.called * 100:.1f}%;--d:{.2 + i * .04:.2f}s'></div></div></div>"
    f"<span class='pct'>{r.actual * 100:.1f}% · {r.called * 100:.1f}%</span></div>"
    for i, (k, r) in enumerate(top.iterrows()))
l, r = pair()
with l:
    with box("Poor Experiences: Actual and Flagged", "pr-pairs", key="recall_low",
             lead=f"For each of the ten largest {what}: the true share of Low reviews, then the share the model flagged."):
        show((pairs or empty("Too few reviews in this view.")) + legend([("actually rated Low", "var(--navy)"), ("flagged Low by the model", ".hatch")]))
        if len(top):
            gap = top["called"] - top["actual"]
            worst = gap.abs().idxmax()
            note(f"For the largest {what}, the share flagged Low closely matches the share that really was Low. The widest gap is "
                 f"{esc(worst)} ({gap[worst] * 100:+.1f} points), where patients' words and their star ratings differ most.")
with r:
    with box(f"{noun} to Review First", "pr-first", key="capture",
             tools=lambda: pick("pr_first_min", PMINS, fmt=pmin_fmt, label="Minimum reviews", width=140),
             lead=f"Average chance of a poor experience, among {what} with at least the chosen number of reviews.") as mn_first:
        rank = g_all[g_all["test_reviews"] >= mn_first].sort_values("chance", ascending=False).head(10)
        if len(rank):
            tips = {k: f"{k}\naverage chance of Low: {x.chance * 100:.1f}%\nactually Low: {x.actual * 100:.1f}%\n{int(x.test_reviews):,} reviews" for k, x in rank.iterrows()}
            show(bars(rank["chance"], lambda x: f"{x * 100:.1f}%", lead=rank.index[0], label_w=180, tall=True, tips=tips)
                 + legend([("highest chance", "var(--navy)"), ("average chance of Low", "var(--blue)")]))
            note(f"{esc(rank.index[0])} has the highest average chance of a poor experience ({rank['chance'].iloc[0] * 100:.1f}%). "
                 f"Start reviews and follow-up calls here.")
        else:
            show(empty("No group has that many reviews."))

TSORT = {"Most reviews": ("test_reviews", False), "Highest chance of Low": ("chance", False),
         "Largest gap": ("gap", False), "Most helpful": ("helpful", False)}


def ttools():
    return (find("pr_q", f"Find a {one}"), pick("pr_sort", list(TSORT), label="Sort", width=170),
            pick("pr_min", PMINS, fmt=pmin_fmt, label="Minimum reviews", width=140))


with box(f"{noun} Table", "predictive-table", key="recall_low", tools=ttools,
         lead=f"Click a row to filter the dashboard to that {one}. Largest gap is the distance between the actual and flagged Low shares.") as (q, sort, mn):
    t = g_all[g_all["test_reviews"] >= mn]
    if q:
        t = t[t.index.str.contains(q, case=False, regex=False)]
    col, asc = TSORT[sort]
    t = t.sort_values(col, ascending=asc).reset_index()
    if len(t):
        for c_ in ["actual", "called", "chance", "helpful", "helpful_pred"]:
            t[c_] = t[c_] * 100
        table(t[[by, "test_reviews", "actual", "called", "chance", "helpful", "helpful_pred"]], "pr_tbl", by,
              "f_cond" if by == "condition_label" else "f_med", height=380,
              column_config={by: st.column_config.TextColumn("Condition" if by == "condition_label" else "Medication", width="medium"),
                             "test_reviews": st.column_config.NumberColumn("Reviews", format="localized"),
                             "actual": st.column_config.ProgressColumn("Actually Low", min_value=0.0, max_value=100.0, format="%.1f%%"),
                             "called": st.column_config.ProgressColumn("Flagged Low", min_value=0.0, max_value=100.0, format="%.1f%%"),
                             "chance": st.column_config.NumberColumn("Chance of Low", format="%.1f%%"),
                             "helpful": st.column_config.NumberColumn("Actually Helpful", format="%.1f%%",
                                                                      help="Share among the most helpful quarter of reviews posted the same month. Conditions with many reviews but few readers per review, such as Birth Control, rarely reach that quarter, so their share is low."),
                             "helpful_pred": st.column_config.NumberColumn("Predicted Helpful", format="%.1f%%", help="Average chance from the helpfulness model")})
    else:
        show(empty(f"No {one} matches."))
