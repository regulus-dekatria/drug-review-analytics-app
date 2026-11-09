"""Rankings: the old dashboard's scatter, nine-rung ladder and rank table."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core import plot_layout
from dash import (MINS, RANK_MIN, box, empty, filters, group_table, hero, hist, kpis, ladder9, min_fmt, note, pair, pct, pick,
                  show, stats, table, view)

hero("Rankings")
f = filters()
c = view(*f)
s = stats(hist(c))
if not s["n"]:
    st.warning("No reviews match these filters.")
    st.stop()
ss = st.session_state
mn = ss.get("rk_min", RANK_MIN)
allm = group_table(*f[:3], "drugName", f[3])
ranked = allm[allm["reviews"] >= mn].copy()
means = np.sort(ranked["mean"].values)
thin = int((allm["reviews"] <= 2).sum())
show(kpis([
    ("Score Needed to Reach the Top 10%", f"{np.quantile(means, .9):.2f}" if len(means) else "-", f"among {len(ranked):,} ranked medications", "top10", "workspace_premium"),
    ("Averages Built on One or Two Reviews", f"{thin:,}", f"{pct(thin / max(len(allm), 1))} of {len(allm):,} medications", "thinavg", "warning")], n=2))

l, r = pair()
with l:
    with box("How Many Reviews Sit Behind Each Average", "rk-scatter", key="rankmin",
             lead=f"Each dot is a medication. Dark dots have at least {RANK_MIN} reviews; the shaded strip marks averages from one or two reviews. Click a dot to filter."):
        fig = go.Figure()
        fig.add_hrect(y0=0.7, y1=2.5, fillcolor="rgba(0,172,193,.14)", line_width=0)
        fig.add_trace(go.Scatter(x=allm["mean"], y=allm["reviews"], mode="markers", text=allm.index, customdata=allm.index,
                                 marker=dict(size=6, color=np.where(allm["reviews"] >= RANK_MIN, "#0D47A1", "#4DD0E1"), opacity=.8, line=dict(width=0)),
                                 hovertemplate="<b>%{text}</b><br>average %{x:.2f}<br>%{y:,} reviews<extra></extra>"))
        fig.update_layout(**plot_layout(360), showlegend=False, clickmode="event+select",
                          xaxis=dict(title="average rating", range=[0.8, 10.2], gridcolor="rgba(13,71,161,.08)", zeroline=False),
                          yaxis=dict(title="reviews behind the average", type="log", gridcolor="rgba(13,71,161,.08)", zeroline=False))
        gen = ss.get("rk_sc_gen", 0)

        def picked():
            pts = ss[f"rk_sc_{gen}"].selection.points
            if pts:
                ss.f_med = pts[0].get("customdata") or pts[0].get("text")
                ss.rk_sc_gen = gen + 1
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=f"rk_sc_{gen}", on_select=picked, selection_mode="points")
        note("Medications with only a few reviews scatter right across the scale, with a crowd of perfect tens. As reviews build up, "
             "averages pull into a narrow band. Treat any top-ranked medication with few reviews as unproven.")
with r:
    with box("What Score It Takes to Rank at Each Level", "rk-ladder", key="top10",
             lead="The average a medication needs at each tenth of the ranking, bottom 10% on the left to top 10% on the right."):
        if len(means) >= 9:
            vals, body = ladder9(means)
            show(body)
            note(f"An average of {vals[4]:.2f} puts a medication in the middle of the {len(ranked):,} ranked; it takes {vals[8]:.2f} to reach the "
                 f"top tenth. The rungs sit at roughly even distances, so each step costs about the same.")
        else:
            show(empty("Too few ranked medications in view."))

with box("Medications by Rank", "rk-table", key="top10", tools=lambda: pick("rk_min", MINS, fmt=min_fmt, label="Minimum reviews", width=140),
         lead="Click a row to filter the dashboard to that medication. Click a column header to sort."):
    if len(ranked):
        ranked["rank"] = [float((means < m).sum()) / len(means) * 100 for m in ranked["mean"]]
        out = ranked.sort_values(["mean", "reviews"], ascending=False).reset_index()
        out["position"] = np.arange(1, len(out) + 1)
        out["high"] = out["high"] * 100
        table(out[["position", "drugName", "dist", "reviews", "mean", "rank", "high"]], "rk_tbl", "drugName", "f_med", height=420, column_config={
            "position": st.column_config.NumberColumn("Position", help=f"Place in the order, 1 is the highest average, of {len(out):,} ranked", format="%d"),
            "drugName": st.column_config.TextColumn("Medication", width="medium"),
            "dist": st.column_config.BarChartColumn("Distribution 1 to 10"),
            "reviews": st.column_config.NumberColumn("Reviews", format="localized"),
            "mean": st.column_config.NumberColumn("Average", format="%.2f"),
            "rank": st.column_config.ProgressColumn("Rank", min_value=0, max_value=100, format="%.0f", help="Better than this percentage of the ranked medications"),
            "high": st.column_config.ProgressColumn("Rated 8+", min_value=0.0, max_value=100.0, format="%.1f%%")})
    else:
        show(empty("No medication has enough reviews to rank."))
