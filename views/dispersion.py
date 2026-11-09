"""Rating Dispersion: the old dashboard's spread histogram, agree/disagree dot plot and extremes chart, then the detail table."""
import numpy as np
import streamlit as st

from dash import (box, columns, diverge, dots, empty, filters, find, group_table, hero, hist, kpis, note, pair, pct, pick,
                  show, stats, table, view)

hero("Rating Dispersion")
f = filters()
c = view(*f)
s = stats(hist(c))
if not s["n"]:
    st.warning("No reviews match these filters.")
    st.stop()
ss = st.session_state
DMINS = [30, 100, 2]
dmin_fmt = lambda v: "Any number" if v == 2 else f"{v}+ reviews"
mn = ss.get("ds_min", 30)
mt = group_table(*f[:3], "drugName", f[3])
mt = mt[(mt["reviews"] >= mn) & (mt["reviews"] > 1)]
typical = float(mt["sd"].median()) if len(mt) else np.nan
show(kpis([
    ("Typical Rating Spread", "-" if np.isnan(typical) else f"{typical:.2f}", f"rating points, across {len(mt):,} medications", "spread", "swap_vert"),
    ("Polarised Review Share", pct(s["r1"] + s["r10"]), "reviews at the lowest or highest score", "polarshare", "contrast")], n=2))

DSORTS = {"Most divided": ("sd", False), "Most agreed": ("sd", True), "Most reviews": ("reviews", False)}
l, r = pair()
with l:
    with box("How Much Patients Disagree, Medication by Medication", "ds-hist", key="spread",
             lead=f"Medications with {dmin_fmt(mn).replace('+ reviews', ' or more reviews').lower()}, grouped by how far their ratings spread from their own average."):
        if len(mt) >= 3:
            edges = np.linspace(0, 4.5, 19)
            counts, _ = np.histogram(mt["sd"].clip(0, 4.499), bins=edges)
            labels = [f"{edges[i]:.1f}" if i % 2 == 0 else "" for i in range(18)]
            show(columns(list(counts), labels, lambda v: f"{v}" if v else "", height=300, marks=[(typical / 4.5 * 100, f"middle medication {typical:.2f}")])
                 + "<div class='label' style='margin-top:6px;text-align:center'>rating points between a typical patient and that medication's own average</div>")
            note(f"Most medications have a spread between {mt['sd'].quantile(.25):.1f} and {mt['sd'].quantile(.75):.1f} rating points. The most "
                 f"a 1 to 10 scale allows is 4.5, so patients often disagree sharply about the same medication.")
        else:
            show(empty("A distribution needs several medications in view. Clear the medication filter to compare spreads."))
with r:
    def tools():
        return (find("ds_q", "Find a medication"), pick("ds_sort", list(DSORTS), label="Sort", width=140),
                pick("ds_min", DMINS, fmt=dmin_fmt, label="Minimum reviews", width=140))
    with box("Medications Patients Agree On, and Medications They Do Not", "ds-dots", key="spread", tools=tools,
             lead="Spread in rating points, every medication on one axis from zero. Scroll inside the panel; hover a dot for its figures.") as (q, sort, _):
        t = mt if not q else mt[mt.index.str.contains(q, case=False, regex=False)]
        col, asc = DSORTS[sort]
        t = t.sort_values(col, ascending=asc)
        show(dots([(k, v.sd, f"{k}\n{v.sd:.2f} rating points of spread over {int(v.reviews):,} reviews\naverage rating {v['mean']:.2f}")
                   for k, v in t.iterrows()], scroll=330))
        note("Consistency is not the same as quality: a medication can be consistently rated poorly, so read the spread next to its average.")

ESORTS = {"Most polarised": ("polar", False), "Least polarised": ("polar", True), "Most rated 1": ("r1", False),
          "Most rated 10": ("r10", False), "Most reviews": ("reviews", False)}
et = mt.assign(polar=mt["r1"] + mt["r10"])
with box("Where Reviews Sit at the Extremes", "ds-ext", key="polar",
         tools=lambda: (find("ex_q", "Find a medication"), pick("ex_sort", list(ESORTS), label="Sort", width=160)),
         lead="The bar reaches left for patients who gave a 1 and right for those who gave a 10; the striped block is everyone else.") as (q, sort):
    t = et if not q else et[et.index.str.contains(q, case=False, regex=False)]
    col, asc = ESORTS[sort]
    t = t.sort_values(col, ascending=asc)
    rows = [(k, v.r1, v.r10, f"{k}\nrated 1: {v.r1 * 100:.1f}%\nrated 2 to 9: {(1 - v.polar) * 100:.1f}%\nrated 10: {v.r10 * 100:.1f}%\n{int(v.reviews):,} reviews")
            for k, v in t.iterrows()]
    show(diverge(rows, label_w=210, scroll=380, legend_items=[("rated 1", "var(--navy)"), ("rated 2 to 9", ".hatch-light"), ("rated 10", "var(--blue)")])
         if rows else empty("No medication matches."))
    note("Two medications can look equally divided while one is mostly loved and the other mostly disliked; the two ends tell them apart.")

if len(mt) >= 2:
    from dash import bars
    div = mt.sort_values("sd", ascending=False).head(10)["sd"]
    agr = mt.sort_values("sd").head(10)["sd"]
    l, r = pair()
    with l:
        with box("Most Divided Medications", "ds-div", key="spread", lead="Largest spread, in rating points (4.5 is the most possible)."):
            show(bars(div, lambda v: f"{v:.2f}", lead=div.index[0], scale=4.5))
            note(f"Patients split most sharply on {div.index[0]}. Expect both glowing and angry reviews, and read a sample of each.")
    with r:
        with box("Most Agreed Medications", "ds-agr", key="spread", lead="Smallest spread, in rating points (4.5 is the most possible)."):
            show(bars(agr, lambda v: f"{v:.2f}", lead=agr.index[0], scale=4.5))
            note(f"Patients rate {agr.index[0]} most consistently. Agreement is not approval: check its average on Rankings.")
