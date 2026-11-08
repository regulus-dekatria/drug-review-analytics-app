"""Average Ratings: what the three averages say, and how each condition is rated."""
import streamlit as st

from core import footer
from dash import columns, empty, esc, filters, group_table, hero, hist, kpis, legend, panel, pct, scope_line, stats, view, not_recorded

hero("Dashboard · Average Ratings", "What the averages say, and what they hide",
     "Three averages describe the same reviews: the mean, the typical score in the middle, and the score chosen most often. "
     "When they disagree, none of them alone describes a real patient.")
cond, med, years = filters()
c = view(cond, med, years)
s = stats(hist(c))
if not s["n"]:
    st.warning("No reviews match these filters.")
    st.stop()
scope_line(cond, med, years, s["n"])
st.markdown(kpis([
    ("Average Rating Score", f"{s['mean']:.2f}", "the mean of every score", "mean", "functions"),
    ("Typical Patient Rating Score", f"{s['median']}", "half scored at or below, half at or above", "median", "align_horizontal_center"),
    ("Most Frequent Patient Rating Score", f"{s['mode']}", "the score chosen most often", "mode", "star")], n=3), unsafe_allow_html=True)

h = hist(c)
pos = lambda v: (v - 0.5) / 10 * 100
body = columns(list(h.values), [str(i) for i in range(1, 11)], lambda v: f"{v:,}", dark=(s["median"] - 1,), soft=(s["mode"] - 1,) if s["mode"] != s["median"] else (),
               height=220, marks=[(pos(s["mean"]), f"mean {s['mean']:.2f}")])
body += legend([("typical score (median)", "var(--navy)"), ("most frequent score", "var(--aqua)"), ("other scores", "var(--blue)")])
panel("Where do the three averages land?", body,
      f"The mean ({s['mean']:.2f}) sits where few patients scored, the typical patient scored {s['median']}, and the most "
      f"common score is {s['mode']}. That gap is the polarisation in the reviews, not an error." if s["mode"] != round(s["mean"]) else
      f"Here the three averages broadly agree, so the mean of {s['mean']:.2f} is a fair summary.",
      key="mean", delay=.05)

nr = not_recorded()
ct = group_table(cond, med, years, "condition_label")
ct = ct.drop(nr, errors="ignore")
f1, f2, f3 = st.columns([1.4, 1, 1])
q = f1.text_input("Find a condition", placeholder="e.g. migraine")
sort = f2.selectbox("Sort", ["Most reviews", "Highest rated", "Lowest rated", "A to Z"])
mn = f3.selectbox("Minimum reviews", [30, 100, 1], format_func=lambda v: "All conditions" if v == 1 else f"{v}+ reviews")
t = ct[ct["reviews"] >= mn]
if q:
    t = t[t.index.str.contains(q, case=False, regex=False)]
t = {"Most reviews": t.sort_values("reviews", ascending=False), "Highest rated": t.sort_values("high", ascending=False),
     "Lowest rated": t.sort_values("high"), "A to Z": t.sort_index()}[sort]

rows = "".join(
    f"<div class='bar' style='--lw:190px;--pw:64px'><span class='name' title='{esc(name)}'>{esc(name)}</span>"
    f"<div class='stack thin' style='flex:1'><div style='width:{r.low * 100:.1f}%;background:var(--navy)'></div>"
    f"<div class='hatch-light' style='width:{(1 - r.low - r.high) * 100:.1f}%'></div>"
    f"<div style='width:{r.high * 100:.1f}%;background:var(--blue)'></div></div><span class='pct'>{r.high * 100:.0f}%</span></div>"
    for name, r in t.head(15).iterrows())
panel("How are medications for each condition rated?",
      (rows or empty("No condition matches."))
      + legend([("rated 1 to 3", "var(--navy)"), ("rated 4 to 7", ".hatch-light"), ("rated 8 to 10", "var(--blue)")]),
      "Almost every bar is thin through the middle: patients rarely choose a middling score. The figure on the right is the "
      "share rated 8 or above. Fifteen shown; the table below lists them all.", key="high8", delay=.1)

st.markdown("<div class='q'>Rating scores by condition treated</div>", unsafe_allow_html=True)
table = t.reset_index()[["condition_label", "dist", "reviews", "mean", "median", "mode", "high"]]
st.dataframe(table, hide_index=True, width="stretch", height=380, column_config={
    "condition_label": st.column_config.TextColumn("Condition", width="medium"),
    "dist": st.column_config.BarChartColumn("Distribution 1 to 10", help="Distinct reviews at each rating, 1 on the left"),
    "reviews": st.column_config.NumberColumn("Reviews", format="%d"),
    "mean": st.column_config.NumberColumn("Average", format="%.2f"),
    "median": st.column_config.NumberColumn("Typical", help="The median score"),
    "mode": st.column_config.NumberColumn("Most frequent"),
    "high": st.column_config.ProgressColumn("Rated 8+", min_value=0.0, max_value=1.0, format="percent")})
st.caption(f"{len(t):,} conditions listed.")
footer()
