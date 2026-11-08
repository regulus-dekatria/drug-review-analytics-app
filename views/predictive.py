"""Predictive Insights: where the models would send the pharmacy team, on reviews they never saw."""
import pandas as pd
import streamlit as st

from core import footer, metrics, predictive_cube
from dash import empty, bars, esc, filters, hero, kpis, legend, panel, pct, not_recorded

hero("Dashboard · Predictive Insights", "Where the models would send the team first",
     "Every figure here comes from the 52,524 test reviews posted in 2016 and 2017, which no model saw in training. "
     "Ratings were hidden from the model; its calls are compared with what patients actually scored.")
cond, med, _ = filters(show_years=False)
pc = predictive_cube()
if pc is None:
    st.error("data/predictive_cube.parquet is missing. Run Notebook 3 Run 2 and copy it from derived/dashboard.")
    st.stop()
v = pc
if cond != "All conditions":
    v = v[v["condition_label"] == cond]
if med != "All medications":
    v = v[v["drugName"] == med]
n = int(v["test_reviews"].sum())
if not n:
    st.warning("No test reviews (2016 and 2017) match these filters.")
    st.stop()
st.caption(f"{n:,} test reviews from 2016 and 2017 · {'all conditions' if cond == 'All conditions' else cond}"
           + ("" if med == "All medications" else f" · {med}") + " · the year filter does not apply on this page")

m = metrics() or {}
cap = (m.get("objective1", {}).get("capture_rate") or {}).get("20%")
st.markdown(kpis([
    ("Actually rated Low", pct(v["actual_low"].sum() / n), "test reviews rated 1 to 3", "recall_low", "sentiment_dissatisfied"),
    ("Called Low by the model", pct(v["pred_low"].sum() / n), "DistilBERT, reading the text only", "severe", "psychology"),
    ("Average chance of Low", pct(v["p_low_sum"].sum() / n), "the model's mean probability", "balacc", "percent"),
    ("Low found reading the top 20%", pct(cap) if cap else "-", "all test reviews, sorted by chance of Low", "capture", "manage_search")]),
    unsafe_allow_html=True)

nr = not_recorded()
by = "condition_label" if cond == "All conditions" else "drugName"
g = v[v["condition_label"] != nr].groupby(by)[["test_reviews", "actual_low", "pred_low", "actual_high", "pred_high", "p_low_sum", "helpful_actual", "helpful_score_sum"]].sum()
g = g[g["test_reviews"] >= (100 if by == "condition_label" else 20)].sort_values("test_reviews", ascending=False)
what = "conditions" if by == "condition_label" else f"medications for {cond}"

left, right = st.columns(2)
with left:
    top = g.head(10)
    rows = "".join(
        f"<div class='bar pair' style='--lw:180px;--pw:96px'><span class='name' title='{esc(k)}'>{esc(k)}</span><div style='flex:1'>"
        f"<div class='track' style='margin-bottom:3px'><div class='fill lead' style='width:{r.actual_low / r.test_reviews * 100:.1f}%;--d:{.15 + i * .04:.2f}s'></div></div>"
        f"<div class='track'><div class='fill b' style='width:{r.pred_low / r.test_reviews * 100:.1f}%;--d:{.2 + i * .04:.2f}s'></div></div></div>"
        f"<span class='pct'>{r.actual_low / r.test_reviews * 100:.0f}% · {r.pred_low / r.test_reviews * 100:.0f}%</span></div>"
        for i, (k, r) in enumerate(top.iterrows()))
    if len(top):
        gap = (top["pred_low"] - top["actual_low"]) / top["test_reviews"]
        worst = gap.abs().idxmax()
        note = (f"Across the largest {what}, the model's Low share tracks the true Low share closely. The widest gap is "
                f"{esc(worst)} ({gap[worst] * 100:+.1f} points), where its reviewers' wording and their stars part ways most.")
    else:
        note = "Too few test reviews in this view."
    panel("Does the model find poor experiences where they really are?" if by == "condition_label" else f"Does the model find poor experiences among medications for {cond}?",
          (rows or empty("Too few test reviews in this view."))
          + legend([("actually rated Low", "var(--navy)"), ("called Low by the model", ".hatch")]),
          note, key="recall_low", delay=.05, lead="Each pair shows one group's true Low share and the share the model flagged.")

with right:
    rank = g.assign(chance=g["p_low_sum"] / g["test_reviews"]).sort_values("chance", ascending=False).head(10)
    panel(f"Which {'conditions' if by == 'condition_label' else 'medications'} would the model send the team to first?",
          bars(rank["chance"], lambda x: f"{x * 100:.0f}%", lead=rank.index[0] if len(rank) else None, label_w=180),
          (f"{esc(rank.index[0])} carries the highest average chance of Low ({rank['chance'].iloc[0] * 100:.0f}%). Sorting the inbox by "
           f"this chance is how the Classify page would triage new messages." if len(rank) else "Too few test reviews."),
          key="capture", delay=.1, lead=f"Average chance of Low, among {what} with enough test reviews.")

st.markdown("<div class='q'>Model calls by group, test years</div>", unsafe_allow_html=True)
t = g.assign(actual=g["actual_low"] / g["test_reviews"], called=g["pred_low"] / g["test_reviews"],
             chance=g["p_low_sum"] / g["test_reviews"], helpful=g["helpful_actual"] / g["test_reviews"],
             helpful_pred=g["helpful_score_sum"] / g["test_reviews"]).reset_index()
st.dataframe(t[[by, "test_reviews", "actual", "called", "chance", "helpful", "helpful_pred"]], hide_index=True, width="stretch", height=360,
             column_config={by: st.column_config.TextColumn("Condition" if by == "condition_label" else "Medication", width="medium"),
                            "test_reviews": st.column_config.NumberColumn("Test reviews", format="%d"),
                            "actual": st.column_config.ProgressColumn("Actually Low", min_value=0.0, max_value=1.0, format="percent"),
                            "called": st.column_config.ProgressColumn("Called Low", min_value=0.0, max_value=1.0, format="percent"),
                            "chance": st.column_config.NumberColumn("Mean chance of Low", format="percent"),
                            "helpful": st.column_config.NumberColumn("Actually helpful", format="percent", help="Share in the top 25% of helpful votes for their month"),
                            "helpful_pred": st.column_config.NumberColumn("Predicted helpful", format="percent", help="Mean chance from the helpfulness model")})
st.caption("Predictions come from Predictive Analytics Run 2. To classify a new message, use Classify a message under Predict.")
footer()
