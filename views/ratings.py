"""Average Ratings: the old dashboard's distribution with three averages, the centred condition bars and the condition table."""
import streamlit as st

from dash import (MINS, box, columns, diverge, empty, filters, find, group_table, hero, hist, kpis, legend, min_fmt,
                  not_recorded, note, pair, pick, show, stats, table, view)

hero("Average Ratings")
f = filters()
c = view(*f)
s = stats(hist(c))
if not s["n"]:
    st.warning("No reviews match these filters.")
    st.stop()
show(kpis([
    ("Average Rating Score", f"{s['mean']:.2f}", "the mean of every score", "mean", "functions"),
    ("Typical Patient Rating Score", f"{s['median']}", "half scored at or below, half at or above", "median", "align_horizontal_center"),
    ("Most Frequent Patient Rating Score", f"{s['mode']}", "the score chosen most often", "mode", "star")], n=3))

ct = group_table(*f[:3], "condition_label", f[3]).drop(not_recorded(), errors="ignore")
SORTS = {"Most reviews": ("reviews", False), "Highest rated": ("high", False), "Lowest rated": ("high", True)}
h = hist(c)
pos = lambda v: (v - 0.5) / 10 * 100
l, r = pair()
with l:
    with box("Rating Scores Distribution", "rt-dist", key="mean", lead="Reviews at each score, with the three averages marked."):
        show(columns(list(h.values), [str(i) for i in range(1, 11)], lambda v: f"{v:,}", dark=(), height=300,
                     marks=[(pos(s["mean"]), f"mean {s['mean']:.2f}"), (pos(s["median"]), f"median {s['median']}", "m2"),
                            (pos(s["mode"]), f"mode {s['mode']}", "m3")])
             + legend([("average (mean)", "var(--ink)"), ("typical patient (median)", "var(--blue)"), ("most common (mode)", "var(--cyan)")]))
        note(f"The mean ({s['mean']:.2f}) lands at a point few patients chose. The typical patient gave {s['median']} and the most common "
             f"score is {s['mode']}. That gap is the polarisation in the reviews, not an error, so quote all three, not the average alone."
             if s["mode"] != round(s["mean"]) else f"Here the three averages broadly agree, so the mean of {s['mean']:.2f} is a fair summary.")
with r:
    def tools():
        return (find("ct_q", "Find a condition"), pick("ct_sort", list(SORTS), label="Sort", width=140),
                pick("ct_min", MINS, fmt=min_fmt, label="Minimum reviews", width=140))
    with box("How Medications for Each Condition Are Rated", "rt-cond", key="high8", tools=tools,
             lead="One bar per condition: rated 1 to 3 reaches left of the line, 8 to 10 right. Hover a bar for its figures.") as (q, sort, mn):
        t = ct[ct["reviews"] >= mn]
        if q:
            t = t[t.index.str.contains(q, case=False, regex=False)]
        col, asc = SORTS[sort]
        t = t.sort_values(col, ascending=asc)
        rows = [(k, v.low, v.high, f"{k}\nrated 1 to 3: {v.low * 100:.1f}%\nrated 4 to 7: {(1 - v.low - v.high) * 100:.1f}%\n"
                                     f"rated 8 to 10: {v.high * 100:.1f}%\n{int(v.reviews):,} reviews") for k, v in t.iterrows()]
        show(diverge(rows, label_w=190, scroll=330,
                     legend_items=[("rated 1 to 3", "var(--navy)"), ("rated 4 to 7", ".hatch-light"), ("rated 8 to 10", "var(--blue)")])
             if rows else empty("No condition matches."))
        note("Almost every bar is thin through the middle: patients rarely give a middling score. The further a bar reaches right, "
             "the better patients rated the medications for that condition.")

TSORTS = {"Most reviews": ("reviews", False), "Highest average": ("mean", False), "Lowest average": ("mean", True), "A to Z": (None, True)}


def ttools():
    return (find("tb_q", "Find a condition"), pick("tb_sort", list(TSORTS), label="Sort", width=150),
            pick("tb_min", MINS, fmt=min_fmt, label="Minimum reviews", width=140))


with box("Rating Scores by Condition Treated", "rt-table", key="high8", tools=ttools,
         lead="The same conditions as numbers. Click a row to filter the dashboard to that condition.") as (q, sort, mn):
    t = ct[ct["reviews"] >= mn]
    if q:
        t = t[t.index.str.contains(q, case=False, regex=False)]
    col, asc = TSORTS[sort]
    t = t.sort_index() if col is None else t.sort_values(col, ascending=asc)
    if len(t):
        out = t.reset_index()[["condition_label", "dist", "reviews", "mean", "median", "mode", "high"]].assign(high=lambda d: d["high"] * 100)
        table(out, "rt_tbl", "condition_label", "f_cond", height=400, column_config={
            "condition_label": st.column_config.TextColumn("Condition", width="medium"),
            "dist": st.column_config.BarChartColumn("Distribution 1 to 10", help="Reviews at each score, 1 on the left"),
            "reviews": st.column_config.NumberColumn("Reviews", format="localized"),
            "mean": st.column_config.NumberColumn("Average", format="%.2f"),
            "median": st.column_config.NumberColumn("Typical Rating", help="The typical patient's score (median)"),
            "mode": st.column_config.NumberColumn("Most Frequent"),
            "high": st.column_config.ProgressColumn("Rated 8+", min_value=0.0, max_value=100.0, format="%.1f%%")})
    else:
        show(empty("No condition matches this search."))
