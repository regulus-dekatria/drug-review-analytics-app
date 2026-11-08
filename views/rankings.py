"""Rankings: which averages can be trusted, and what score each level takes."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core import footer
from dash import empty, RANK_MIN, esc, filters, group_table, hero, hist, kpis, panel, pct, scope_line, stats, view

hero("Dashboard · Rankings", "Where a medication stands",
     "An average only ranks fairly once enough reviews sit behind it. This page separates the averages that can be "
     "compared from the ones that cannot, then shows what score each level of the line-up takes.")
cond, med, years = filters()
c = view(cond, med, years)
s = stats(hist(c))
if not s["n"]:
    st.warning("No reviews match these filters.")
    st.stop()
scope_line(cond, med, years, s["n"])
mn = st.selectbox("Rank medications with at least", [RANK_MIN, 100, 1], format_func=lambda v: "any number of reviews" if v == 1 else f"{v} reviews")
allm = group_table(cond, med, years, "drugName")
ranked = allm[allm["reviews"] >= mn].copy()
means = np.sort(ranked["mean"].values)
thin = int((allm["reviews"] <= 2).sum())
st.markdown(kpis([
    ("Score Needed to Reach the Top 10%", f"{np.quantile(means, .9):.2f}" if len(means) else "-", f"among {len(ranked):,} ranked medications", "top10", "workspace_premium"),
    ("Averages Built on One or Two Reviews", f"{thin:,}", f"{pct(thin / max(len(allm), 1))} of {len(allm):,} medications", "thinavg", "warning")], n=2),
    unsafe_allow_html=True)

left, right = st.columns([1.15, 1])
with left:
    st.markdown("<div class='q'>Business question</div><div class='qt'>How many reviews sit behind each average?</div>", unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_hrect(y0=0.7, y1=2.5, fillcolor="rgba(0,172,193,.14)", line_width=0)
    fig.add_trace(go.Scattergl(x=allm["mean"], y=allm["reviews"], mode="markers", text=allm.index,
                               marker=dict(size=6, color=np.where(allm["reviews"] >= RANK_MIN, "#0D47A1", "#4DD0E1"), opacity=.75,
                                           line=dict(width=0)),
                               hovertemplate="<b>%{text}</b><br>average %{x:.2f}<br>%{y:,} reviews<extra></extra>"))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(224,247,250,.6)",
                      font=dict(family="IBM Plex Sans", color="#0B2545"), showlegend=False,
                      xaxis=dict(title="average rating", range=[0.8, 10.2], gridcolor="rgba(13,71,161,.08)"),
                      yaxis=dict(title="reviews behind the average", type="log", gridcolor="rgba(13,71,161,.08)"))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.markdown(f"<div class='note'>Dots near the bottom rest on a handful of reviews and spread right across the width, with a crowd of "
                f"perfect tens on the right. Dots higher up pull into a narrow band. The shaded strip marks one and two review "
                f"averages; dark dots clear the {RANK_MIN}-review threshold.</div>", unsafe_allow_html=True)

with right:
    if len(means) >= 5:
        steps = [(10, "bottom 10%"), (30, "bottom 30%"), (50, "middle"), (70, "top 30%"), (90, "top 10%")]
        vals = [np.quantile(means, p / 100) for p, _ in steps]
        lo, hi = vals[0] - .3, vals[-1] + .3
        rungs = "".join(f"<div class='rung{' strong up' if p == 50 else ''}' style='left:{(v - lo) / (hi - lo) * 100:.1f}%'><i></i>"
                        f"<b>{v:.2f}</b><small>{lab}</small></div>" for (p, lab), v in zip(steps, vals))
        body = f"<div class='ladder' style='margin-top:58px'>{rungs}</div><div class='label' style='text-align:center'>average rating of a medication</div>"
        note = (f"A medication averaging {vals[2]:.2f} sits in the middle of the {len(ranked):,} ranked; it takes {vals[4]:.2f} "
                f"to reach the top tenth. Read any medication's average against these rungs to place it.")
    else:
        body, note = empty("Too few ranked medications in view."), "Widen the filters to build the ladder."
    panel("What score does it take to rank at each level?", body, note, key="top10", delay=.08)

st.markdown("<div class='q'>Medications by rank</div>", unsafe_allow_html=True)
if len(ranked):
    ranked["rank"] = [float((means < m).sum()) / len(means) * 100 for m in ranked["mean"]]
    out = ranked.sort_values("mean", ascending=False).reset_index()[["drugName", "mean", "rank", "reviews", "dist", "sd"]]
    st.dataframe(out, hide_index=True, width="stretch", height=400, column_config={
        "drugName": st.column_config.TextColumn("Medication", width="medium"),
        "mean": st.column_config.NumberColumn("Average", format="%.2f"),
        "rank": st.column_config.ProgressColumn("Rank", min_value=0, max_value=100, format="%.0f", help="Better than this percentage of the ranked medications"),
        "reviews": st.column_config.NumberColumn("Reviews", format="%d"),
        "dist": st.column_config.BarChartColumn("Votes 1 to 10"),
        "sd": st.column_config.NumberColumn("Spread", format="%.2f")})
footer()
