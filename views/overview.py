"""Overview: the old dashboard's headline figures and top-10 panels, then satisfaction and reliability."""
import numpy as np
import pandas as pd
import streamlit as st

from core import tip
from dash import (BANDS, RANK_MIN, bars, box, empty, esc, filters, group_table, hero, hist, kpis, legend, not_recorded, note,
                  pair, show, stats, view)

hero("Patient Drug Reviews")
f = filters()
c = view(*f)
s = stats(hist(c))
if not s["n"]:
    st.warning("No reviews match these filters. Widen the years, ratings, condition or medication.")
    st.stop()
nr = not_recorded()
meds = group_table(*f[:3], "drugName", f[3])
conds = group_table(*f[:3], "condition_label", f[3]).drop(nr, errors="ignore")
votes = int(c["helpful_votes"].sum())
spread = meds.loc[(meds["reviews"] >= RANK_MIN) & (meds["reviews"] > 1), "sd"]
show(kpis([
    ("Reviews", f"{s['n']:,}", "one per patient", "reviews", "forum"),
    ("Medications", f"{len(meds):,}", "brand and generic counted separately", "meds", "medication"),
    ("Conditions", f"{len(conds):,}", "named conditions", "conds", "stethoscope"),
    ("Helpful Votes", f"{votes:,}", "marked by readers", "avgvotes", "thumb_up"),
    ("Average Number of Helpful Votes", f"{votes / s['n']:.1f}", "per review", "avgvotes", "functions")], n=5))
show(kpis([
    ("Average Rating Score", f"{s['mean']:.2f}", "the mean of every score", "mean", "star_half"),
    ("Typical Patient Rating Score", f"{s['median']}", "the middle score", "median", "align_horizontal_center"),
    ("Most Frequent Rating Score", f"{s['mode']}", "chosen most often", "mode", "star"),
    ("Polarised Review Share", f"{(s['r1'] + s['r10']) * 100:.1f}%", "rated 1 or 10", "polarshare", "contrast"),
    ("Typical Rating Spread", f"{spread.median():.2f}" if len(spread) else "-", f"rating points, medications with {RANK_MIN}+ reviews", "spread", "swap_vert")], n=5))

n = s["n"]
fmt = lambda v: f"{int(v):,} · {v / n * 100:.1f}%"
tips = lambda t: {k: f"{k}\n{int(r.reviews):,} reviews · {r.reviews / n * 100:.1f}% of the reviews in view\naverage {r['mean']:.2f}" for k, r in t.iterrows()}
top_c = conds.sort_values("reviews", ascending=False).head(10)
top_m = meds.sort_values("reviews", ascending=False).head(10)
l, r = pair()
with l:
    with box("Top 10 Conditions by Volume", "ov-conds", key="conds", lead="The ten conditions with the most reviews, longest bar first."):
        show(bars(top_c["reviews"], fmt, lead=top_c.index[0] if len(top_c) else None, pct_w=128, tips=tips(top_c))
             if len(top_c) else empty("Only reviews without a recorded condition match."))
        if len(top_c) > 1:
            note(f"{top_c.index[0]} holds {top_c['reviews'].iloc[0] / n * 100:.1f}% of all reviews, {top_c['reviews'].iloc[0] / top_c['reviews'].iloc[1]:.1f} "
                 f"times as many as {top_c.index[1]}. Totals lean toward it, so choose a condition before comparing medications.")
with r:
    with box("Top 10 Medications by Volume", "ov-meds", key="meds", lead="The ten medications with the most reviews, longest bar first."):
        show(bars(top_m["reviews"], fmt, lead=top_m.index[0] if len(top_m) else None, pct_w=128, tips=tips(top_m)))
        if len(top_m):
            note(f"The ten largest medications hold only {top_m['reviews'].sum() / n * 100:.1f}% of reviews: no single product dominates "
                 f"the feedback the way one condition does.")

pol = s["r1"] + s["r10"]
mid = 1 - pol
stack = (f"<div class='stack'><div style='width:{s['r1'] * 100:.1f}%;background:var(--navy)'>{s['r1'] * 100:.1f}%</div>"
         f"<div class='hatch-light' style='width:{mid * 100:.1f}%'><span class='lbl'>{mid * 100:.1f}%</span></div>"
         f"<div style='width:{s['r10'] * 100:.1f}%;background:var(--cyan)'>{s['r10'] * 100:.1f}%</div></div>"
         + legend([("rated 1, the lowest score", "var(--navy)"), ("rated 2 to 9", ".hatch-light"), ("rated 10, the highest score", "var(--cyan)")]))
with box("Patient Satisfaction", "ov-sat", key="polarshare", lead="Share of reviews at each end of the 1 to 10 scale."):
    show(stack)
    note(f"{pol * 100:.1f}% of patients gave the lowest or the highest score, so the {s['mean']:.2f} average is a score few of them "
         f"actually gave. When comparing medications, look at how many patients rated them 1 as well as at the average."
         if pol >= .3 else f"Only {pol * 100:.1f}% of patients gave an extreme score here, so the {s['mean']:.2f} average is a fair summary.")

by = "condition_label" if f[0] == "All conditions" else "drugName"
groups = (top_c if by == "condition_label" else top_m)
high = groups["high"].sort_values(ascending=False) if len(groups) >= 2 else pd.Series(dtype=float)
funnel = []
for lo, hi, label in BANDS:
    sub = meds[(meds["reviews"] >= lo) & (meds["reviews"] <= hi)]
    funnel.append((label, float(sub["mean"].std(ddof=0)) if len(sub) > 1 else np.nan, float((sub["mean"] >= 9.9999).mean()) if len(sub) else np.nan))
l, r = pair()
with l:
    noun = "Conditions" if by == "condition_label" else "Medications"
    with box(f"Lowest Rated {noun}", "ov-low", key="high8", lead=f"Share of reviews rated 8 or above, ten largest {noun.lower()}."):
        if len(high):
            low = high.index[-1]
            show(bars(high, lambda v: f"{v * 100:.1f}%", lead=low))
            rest = high.drop(low)
            note(f"{low} stands apart: only {high.iloc[-1] * 100:.1f}% of its reviews are 8 or above, against {rest.min() * 100:.1f}% to "
                 f"{rest.max() * 100:.1f}% for the others. Read its reviews first." if high.iloc[-1] < rest.min() - .05 else
                 f"Satisfaction runs from {high.min() * 100:.1f}% ({low}) to {high.max() * 100:.1f}% ({high.index[0]}). Start reading from the bottom.")
        else:
            show(empty("Too few groups in this view to compare."))
with r:
    with box("Reviews Needed for a Reliable Average", "ov-funnel", key="spread",
             lead="How far medication averages spread out (standard deviation), by how many reviews each has."):
        fu = [x for x in funnel if pd.notna(x[1])]
        if len(fu) >= 2:
            hmax = max(x[1] for x in fu)
            cols = "".join(f"<div class='col'><div class='v'>{sd:.2f}</div><div class='c{' dark' if i >= 4 else ' hatch'}' style='height:{sd / hmax * 82:.1f}%'></div></div>"
                           if pd.notna(sd) else "<div class='col'><div class='v'>-</div></div>" for i, (_, sd, _) in enumerate(funnel))
            labs = "".join(f"<div><b>{b}</b>{'' if pd.isna(p) else f'{p * 100:.1f}% at 10.0'}</div>" for b, _, p in funnel)
            show(f"<div class='cols'>{cols}</div><div class='colx'>{labs}</div>"
                 + legend([(f"{RANK_MIN} reviews or more: safe to compare", "var(--navy)"), ("fewer: not enough reviews yet", ".hatch")]))
            p0 = funnel[0][2]
            note(f"Averages from one or two reviews jump around, and {p0 * 100:.1f}% of them are a perfect 10.0. They settle past {RANK_MIN} "
                 f"reviews, so only rank or promote medications with at least that many." if pd.notna(p0) else
                 f"Averages settle as reviews build up; rank only medications with {RANK_MIN} or more reviews.")
        else:
            show(empty("Too few medications in this view to compare their averages."))

# ---- headline figures from the review text analysis and the predictive models
from core import metrics, predictive_cube, reviews_analysis
from dash import title_case

ra = reviews_analysis()
pc = predictive_cube()
l, r = pair()
with l:
    if ra:
        scope = f[0] if f[0] in ra["views"] else "All conditions"
        rv = ra["views"][scope]
        sn = rv["sentiment"]
        neu = sn.get("neutral", max(0.0, 100 - sn["positive"] - sn["negative"]))
        wl = pd.Series(rv["watchlist"]).sort_values(ascending=False)
        with box("Reviews Analysis", "ov-nlp", key="sentiment",
                 lead=f"What the review text says, {'for all conditions' if scope == 'All conditions' else 'for ' + scope}. "
                      "Text figures follow the condition filter only, for the ten largest conditions."):
            show(f"<div class='stack' style='height:34px'>"
                 f"<div style='width:{sn['negative']:.1f}%;background:var(--navy)' data-tip='negative wording&#10;{sn['negative']:.1f}% of reviews'>{sn['negative']:.1f}%</div>"
                 f"<div class='hatch-light' style='width:{neu:.1f}%' data-tip='neutral wording&#10;{neu:.1f}% of reviews'></div>"
                 f"<div style='width:{sn['positive']:.1f}%;background:var(--cyan)' data-tip='positive wording&#10;{sn['positive']:.1f}% of reviews'>{sn['positive']:.1f}%</div></div>"
                 + legend([("negative wording", "var(--navy)"), ("neutral", ".hatch-light"), ("positive wording", "var(--cyan)")])
                 + f"<div class='mini'><div><span>Wording matches rating</span><b>{rv['words_vs_score']['agreement']:.1f}%</b></div>"
                   f"<div><span>Most mentioned topic</span><b>{esc(title_case(wl.index[0]))}</b><small>{wl.iloc[0]:.1f}% of reviews</small></div></div>")
            st.page_link("views/insights.py", label="Open Reviews Analysis", icon=":material/arrow_forward:")
            note(f"Patients mention {title_case(wl.index[0])} more than any other topic. Where the wording and the star rating "
                 f"disagree, the review is usually mixed and worth reading in full.")
with r:
    if pc is not None:
        pv = pc if f[0] == "All conditions" else pc[pc["condition_label"] == f[0]]
        if f[1] != "All medications":
            pv = pv[pv["drugName"] == f[1]]
        tn = int(pv["test_reviews"].sum())
        mm = metrics() or {}
        capr = (mm.get("objective1", {}).get("capture_rate") or {}).get("20%")
        with box("Predictive Insights", "ov-pred", key="capture",
                 lead="How the rating model performs on 2016 and 2017 reviews it never saw. Follows the condition and medication filters, not years or ratings."):
            if tn:
                al, fl = pv["actual_low"].sum() / tn, pv["pred_low"].sum() / tn
                gp = pv[pv["condition_label"] != nr].groupby("condition_label")[["test_reviews", "p_low_sum"]].sum()
                gp = gp[gp["test_reviews"] >= 100]
                first = (gp["p_low_sum"] / gp["test_reviews"]).sort_values(ascending=False)
                show(bars(pd.Series({"Actually rated Low": al, "Flagged Low by the model": fl}), lambda x: f"{x * 100:.1f}%", lead="Actually rated Low", label_w=190)
                     + f"<div class='mini'><div><span>Low found in the top 20%</span><b>{capr * 100:.1f}%</b><small>reading in arrival order finds 20%</small></div>"
                       + (f"<div><span>Condition to review first</span><b>{esc(first.index[0])}</b><small>{first.iloc[0] * 100:.1f}% average chance of Low</small></div>" if len(first) else "")
                       + "</div>")
                st.page_link("views/predictive.py", label="Open Predictive Insights", icon=":material/arrow_forward:")
                note(f"The model flags {fl * 100:.1f}% of reviews as poor experiences against {al * 100:.1f}% that truly were. Sorting the inbox by "
                     f"its chance of Low lets a team find most poor experiences while reading only a fifth of the messages.")
            else:
                show(empty("No 2016 or 2017 reviews match these filters."))
