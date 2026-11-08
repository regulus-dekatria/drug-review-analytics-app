"""Rating Dispersion: how much patients disagree, medication by medication."""
import numpy as np
import pandas as pd
import streamlit as st

from core import footer
from dash import empty, columns, filters, group_table, hero, hist, kpis, panel, pct, scope_line, stats, view

hero("Dashboard · Rating Dispersion", "How much patients disagree",
     "Two measures carry this page. The spread is how far a typical rating sits from a medication's own average; the "
     "polarised share is the same disagreement in plain numbers: reviews at 1 or 10.")
cond, med, years = filters()
c = view(cond, med, years)
s = stats(hist(c))
if not s["n"]:
    st.warning("No reviews match these filters.")
    st.stop()
scope_line(cond, med, years, s["n"])
mn = st.selectbox("Medications with at least", [30, 100, 2], format_func=lambda v: "more than one review" if v == 2 else f"{v} reviews")
mt = group_table(cond, med, years, "drugName")
mt = mt[(mt["reviews"] >= mn) & (mt["reviews"] > 1)]
typical = float(mt["sd"].median()) if len(mt) else np.nan
st.markdown(kpis([
    ("Typical Rating Spread", "-" if np.isnan(typical) else f"{typical:.2f}", f"middle of {len(mt):,} medications, in rating points", "spread", "swap_vert"),
    ("Polarised Review Share", pct(s["r1"] + s["r10"]), "reviews rated 1 or 10", "polarshare", "contrast")], n=2), unsafe_allow_html=True)

left, right = st.columns(2)
with left:
    if len(mt) >= 3:
        edges = np.linspace(0, 4.5, 19)
        counts, _ = np.histogram(mt["sd"].clip(0, 4.499), bins=edges)
        labels = [f"{edges[i]:.1f}" if i % 3 == 0 else "" for i in range(18)]
        body = columns(list(counts), labels, lambda v: f"{v}" if v else "", height=230,
                       marks=[(typical / 4.5 * 100, f"middle {typical:.2f}")])
        body += "<div class='label' style='margin-top:6px'>rating points between a typical patient and the medication's own average</div>"
        note = (f"Most medications sit between {mt['sd'].quantile(.25):.1f} and {mt['sd'].quantile(.75):.1f} rating points of spread. "
                f"On a 1 to 10 scale the largest possible is 4.5, so a typical spread of {typical:.2f} means patients often disagree sharply.")
    else:
        body, note = empty("A distribution needs several medications in view."), "Clear the medication filter to compare spreads."
    panel("How much do patients disagree, medication by medication?", body, note, key="spread", delay=.05)

with right:
    sort = st.selectbox("Order", ["Most divided", "Most agreed", "Most reviews"], key="ds_sort")
    view_t = {"Most divided": mt.sort_values("sd", ascending=False), "Most agreed": mt.sort_values("sd"),
              "Most reviews": mt.sort_values("reviews", ascending=False)}[sort]
    st.markdown("<div class='q'>Medications patients agree on, and medications they do not</div>", unsafe_allow_html=True)
    st.dataframe(view_t.reset_index()[["drugName", "sd", "mean", "reviews"]], hide_index=True, width="stretch", height=330, column_config={
        "drugName": st.column_config.TextColumn("Medication", width="medium"),
        "sd": st.column_config.ProgressColumn("Spread", min_value=0.0, max_value=4.5, format="%.2f", help="Rating points; 4.5 is the most a 1 to 10 scale allows"),
        "mean": st.column_config.NumberColumn("Average", format="%.2f"),
        "reviews": st.column_config.NumberColumn("Reviews", format="%d")})
    st.caption("Consistency is not the same as quality: read the spread next to the average.")

st.markdown("<div class='q'>Where reviews sit at the extremes</div>", unsafe_allow_html=True)
exs = st.selectbox("Order", ["Most polarised", "Least polarised", "Most rated 1", "Most rated 10", "Most reviews"], key="ex_sort")
et = mt.assign(polar=mt["r1"] + mt["r10"])
et = {"Most polarised": et.sort_values("polar", ascending=False), "Least polarised": et.sort_values("polar"),
      "Most rated 1": et.sort_values("r1", ascending=False), "Most rated 10": et.sort_values("r10", ascending=False),
      "Most reviews": et.sort_values("reviews", ascending=False)}[exs]
st.dataframe(et.reset_index()[["drugName", "r1", "r10", "polar", "reviews"]], hide_index=True, width="stretch", height=330, column_config={
    "drugName": st.column_config.TextColumn("Medication", width="medium"),
    "r1": st.column_config.ProgressColumn("Rated 1", min_value=0.0, max_value=1.0, format="percent"),
    "r10": st.column_config.ProgressColumn("Rated 10", min_value=0.0, max_value=1.0, format="percent"),
    "polar": st.column_config.ProgressColumn("Rated 1 or 10", min_value=0.0, max_value=1.0, format="percent"),
    "reviews": st.column_config.NumberColumn("Reviews", format="%d")})
st.caption("Two medications can look equally divided while one is mostly loved and the other mostly disliked; the two ends separate those cases.")
footer()
