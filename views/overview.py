"""Overview: the descriptive dashboard, recalculated live from the summary table built in Notebook 3."""
import numpy as np
import pandas as pd
import streamlit as st

from core import footer, overview_cube, overview_meta, tip

BANDS = [(1, 2, "1 to 2"), (3, 5, "3 to 5"), (6, 10, "6 to 10"), (11, 30, "11 to 30"), (31, 100, "31 to 100"), (101, 10**9, "Over 100")]
RANK_MIN = 30

from dash import filters, hero, kpis, panel, bars, scope_line, not_recorded, empty

cube = overview_cube()
meta = overview_meta() or {}
NOT_RECORDED = not_recorded()
hero("Overview · Descriptive analytics", "Patient drug reviews",
     "Built for pharmacy managers and drug safety teams deciding which medications to compare, stock and investigate, "
     "using distinct Drugs.com reviews from 2008 to 2017.")
cond, med, years = filters()


@st.cache_data(show_spinner=False)
def compute(cond, med, years):
    c = cube
    if cond != "All conditions":
        c = c[c["condition_label"] == cond]
    if med != "All medications":
        c = c[c["drugName"] == med]
    c = c[c["review_year"].between(*years)]
    c = c[c["reviews"] > 0]
    n = int(c["reviews"].sum())
    if n == 0:
        return None
    hist = c.groupby("rating")["reviews"].sum().reindex(range(1, 11), fill_value=0)
    cum = hist.cumsum()
    g = c.assign(rs=c["rating"] * c["reviews"]).groupby("drugName")[["reviews", "rs"]].sum()
    g["mean"] = g["rs"] / g["reviews"]
    funnel = []
    for lo, hi, label in BANDS:
        sub = g[(g["reviews"] >= lo) & (g["reviews"] <= hi)]
        funnel.append({"band": label, "medications": len(sub),
                       "sd": float(sub["mean"].std(ddof=0)) if len(sub) > 1 else np.nan,
                       "perfect": float((sub["mean"] >= 9.9999).mean()) if len(sub) else np.nan})
    # Visual 2 and 4 group by condition, or by medication once a condition is chosen.
    by = "condition_label" if cond == "All conditions" else "drugName"
    groups = c.groupby(by)["reviews"].sum().sort_values(ascending=False)
    groups = groups.drop(NOT_RECORDED, errors="ignore")
    top = groups.head(10)
    high = (c[c["rating"] >= 8].groupby(by)["reviews"].sum().reindex(top.index, fill_value=0) / top).sort_values(ascending=False)
    return {"n": n, "mean": float((hist.index * hist).sum() / n), "median": int(hist.index[(cum >= n / 2).values][0]),
            "mode": int(hist.idxmax()), "r1": hist[1] / n, "r10": hist[10] / n, "meds": len(g),
            "thin": int((g["reviews"] <= 2).sum()), "funnel": funnel, "by": by, "top": top, "high": high}


r = compute(cond, med, years)
if r is None:
    st.warning("No reviews match these filters. Widen the years or choose another condition or medication.")
    st.stop()

scope_line(cond, med, years, r["n"])

thin_share = r["thin"] / r["meds"] if r["meds"] else 0
st.markdown(kpis([
    ("Reviews", f"{r['n']:,}", "distinct, after removing brand and generic copies", "reviews", "forum"),
    ("Average Rating Score", f"{r['mean']:.2f}", f"typical score {r['median']}, most frequent {r['mode']}", "mean", "star_half"),
    ("Polarised Review Share", f"{(r['r1'] + r['r10']) * 100:.1f}%", "reviews rated 1 or 10", "polarshare", "contrast"),
    ("Averages Built on One or Two Reviews", f"{thin_share * 100:.1f}%", f"{r['thin']:,} of {r['meds']:,} medications", "thinavg", "warning")]),
    unsafe_allow_html=True)


left, right = st.columns(2)
with left:
    mid = 1 - r["r1"] - r["r10"]
    stack = (f"<div class='stack'><div style='width:{r['r1'] * 100:.1f}%;background:var(--navy)'>{r['r1'] * 100:.1f}%</div>"
             f"<div class='hatch-light' style='width:{mid * 100:.1f}%'><span class='lbl'>{mid * 100:.1f}%</span></div>"
             f"<div style='width:{r['r10'] * 100:.1f}%;background:var(--cyan)'>{r['r10'] * 100:.1f}%</div></div>"
             f"<div class='legend'><span><i style='background:var(--navy)'></i>rated 1, the lowest score</span>"
             f"<span><i class='hatch-light'></i>rated 2 to 9</span>"
             f"<span><i style='background:var(--cyan)'></i>rated 10, the highest score</span></div>")
    pol = r["r1"] + r["r10"]
    note1 = (f"{pol * 100:.1f}% of reviews sit at the two ends of the scale, so the {r['mean']:.2f} average describes a score few "
             f"reviewers actually gave. Compare medications on their share of extreme ratings as well as their average."
             if pol >= 0.3 else
             f"Only {pol * 100:.1f}% of reviews sit at the extremes here, so the {r['mean']:.2f} average is a fair summary of this view.")
    panel("How satisfied are reviewers, and does the average tell the story?", stack, note1, "polarshare", .1)

    fu = pd.DataFrame(r["funnel"])
    shown = fu.dropna(subset=["sd"])
    if len(shown) >= 2:
        hmax = shown["sd"].max()
        cols = "".join(f"<div class='col'><div class='v'>{row.sd:.2f}</div>"
                       f"<div class='c{' dark' if i >= 4 else ' hatch'}' style='height:{row.sd / hmax * 82:.1f}%;--d:{0.2 + i * 0.05:.2f}s'></div></div>"
                       if pd.notna(row.sd) else "<div class='col'><div class='v'>-</div></div>"
                       for i, row in enumerate(fu.itertuples()))
        labels = "".join(f"<div><b>{row.band}</b>{('' if pd.isna(row.perfect) else f'{row.perfect * 100:.1f}% at 10.0')}</div>" for row in fu.itertuples())
        body = (f"<div class='label'>Spread of medication averages (standard deviation), by reviews behind each average {tip('spread')}</div>"
                f"<div class='cols'>{cols}</div><div class='colx'>{labels}</div>"
                f"<div class='legend'><span><i style='background:var(--navy)'></i>past the {RANK_MIN}-review ranking threshold {tip('rankmin')}</span>"
                f"<span><i class='hatch'></i>below it: not yet evidence</span></div>")
        p0 = fu.iloc[0]
        note3 = (f"Averages built on one or two reviews scatter widely, and {p0.perfect * 100:.1f}% of them sit at a perfect 10.0. "
                 f"The scatter levels off beyond {RANK_MIN} reviews, so only medications past that line should be ranked or promoted."
                 if pd.notna(p0.perfect) else
                 f"The scatter narrows as reviews accumulate; rank only medications with {RANK_MIN} or more reviews.")
    else:
        body = empty("Too few medications in this view to compare their averages.")
        note3 = "Choose All medications, or a larger condition, to see how the spread of averages narrows as reviews accumulate."
    panel("How many reviews does an average need before it can be trusted?", body, note3, "thinavg", .2)

with right:
    top = r["top"]
    what = "conditions" if r["by"] == "condition_label" else f"medications for {cond}"
    if len(top):
        body2 = bars(top, lambda v: f"{int(v):,} · {v / r['n'] * 100:.1f}%", lead=top.index[0], pct_w=128)
        second = top.iloc[1] if len(top) > 1 else None
        note2 = (f"{top.index[0]} holds {top.iloc[0] / r['n'] * 100:.1f}% of distinct reviews"
                 + (f", {top.iloc[0] / second:.1f} times {top.index[1]} in second place." if second else ".")
                 + (" Any figure for all conditions leans toward it, so filter by condition before comparing medications."
                    if r["by"] == "condition_label" else " Figures for this condition lean toward it."))
    else:
        body2, note2 = empty("Only reviews without a recorded condition match."), "Choose a named condition."
    panel("Where is the feedback concentrated?" if r["by"] == "condition_label" else f"Which medications hold the feedback for {cond}?",
          body2, note2, "reviews", .15)

    high = r["high"]
    if len(high) >= 2:
        low_name = high.index[-1]
        body4 = (f"<div class='label'>Share of reviews rated 8 or above, ten largest {what} {tip('high8')}</div>"
                 + bars(high, lambda v: f"{v * 100:.1f}%", lead=low_name))
        rest = high.drop(low_name)
        note4 = (f"{low_name} stands apart, with only {high.iloc[-1] * 100:.1f}% of reviews rated 8 or above while the others range "
                 f"from {rest.min() * 100:.1f}% to {rest.max() * 100:.1f}%. Drug safety teams should read its reviews first."
                 if high.iloc[-1] < rest.min() - 0.05 else
                 f"The share rated 8 or above ranges from {high.min() * 100:.1f}% ({low_name}) to {high.max() * 100:.1f}% "
                 f"({high.index[0]}); start reading at the bottom of the list.")
    else:
        body4, note4 = empty("Too few groups in this view to compare."), "Widen the filters to compare satisfaction."
    panel(f"Which {'conditions' if r['by'] == 'condition_label' else 'medications'} are rated lowest?", body4, note4, "high8", .25)

with st.expander("How these figures are counted"):
    st.markdown(f"""
- **Opinions** use distinct reviews: a review published under both a brand and a generic name counts once.
- **Conditions** that held a page fragment in the source are grouped as "{NOT_RECORDED}" and left out of the condition charts.
- **Medications** keep brand and generic names separate.
- The figures are recalculated from a summary table built in the notebook *Building the Final Analytics Dashboard*
  (run {meta.get('run', '?')}), so every filter changes every card and chart.
""")

footer()
