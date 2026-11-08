"""Volume Analysis: how much feedback there is, and where it sits."""
import streamlit as st

from core import footer
from dash import RAMP7, bars, columns, filters, group_table, hero, hist, kpis, legend, panel, pct, scope_line, view, not_recorded

hero("Dashboard · Volume Analysis", "How much feedback there is, and where it sits",
     "Counts of medications, conditions and reviews use every record, copies included, as in the original dashboard. "
     "The rating distribution uses distinct reviews, because it measures opinions.")
cond, med, years = filters()
c = view(cond, med, years)
if c["reviews"].sum() == 0:
    st.warning("No reviews match these filters.")
    st.stop()
has_records = "records" in c.columns
rec_col = "records" if has_records else "reviews"
n_rev, n_rec = int(c["reviews"].sum()), int(c[rec_col].sum())
votes = int(c["helpful_votes_records"].sum()) if "helpful_votes_records" in c else int(c["helpful_votes"].sum())
scope_line(cond, med, years, n_rec, "records")

nr = not_recorded()
meds_t = group_table(cond, med, years, "drugName")
cond_t = group_table(cond, med, years, "condition_label")
st.markdown(kpis([
    ("Records", f"{n_rec:,}", "every row, brand and generic copies included", "records", "database"),
    ("Distinct reviews", f"{n_rev:,}", "one per patient opinion", "reviews", "forum"),
    ("Medications", f"{c['drugName'].nunique():,}", "brand and generic counted separately", "meds", "medication"),
    ("Conditions", f"{c.loc[c['condition_label'] != nr, 'condition_label'].nunique():,}", "named conditions", "conds", "stethoscope"),
    ("Helpful votes", f"{votes:,}", f"{votes / max(n_rec, 1):.1f} per record on average", "avgvotes", "thumb_up")], n=5), unsafe_allow_html=True)

left, right = st.columns(2)
with left:
    h = hist(c)
    share = h / h.sum()
    body = columns(list(h.values), [str(i) for i in range(1, 11)], lambda v: f"{v:,}", dark=(0, 9),
                   sub=[f"{s * 100:.1f}%" for s in share])
    panel("How are ratings spread across the 1 to 10 scale?", body,
          f"Ratings of 1 and 10 together hold {pct(share[1] + share[10])} of distinct reviews, while the middle of the scale "
          f"stays thin. Most reviewers write when they are delighted or disappointed.",
          key="polar", delay=.05, lead="Distinct reviews at each rating. The two ends are darker because that is where reviews collect.")

    by_c = c[c["condition_label"] != nr].groupby("condition_label")[rec_col].sum().sort_values(ascending=False)
    top_c = by_c.head(10)
    rest = by_c.iloc[10:].sum()
    series = top_c.copy()
    other_label = f"All other conditions ({max(len(by_c) - 10, 0):,})"
    if rest > 0:
        series[other_label] = rest
    base = by_c.sum() or 1
    panel("Which conditions do patients write about most?",
          bars(series, lambda v: f"{int(v):,} · {v / base * 100:.1f}%", lead=top_c.index[0] if len(top_c) else None,
               pct_w=128, other=other_label, scale=series.max()),
          f"The ten largest conditions account for {pct(top_c.sum() / base)} of the records in view; the striped bar holds every other condition combined.",
          key="conds", delay=.12)

with right:
    by_m = c.groupby("drugName")[rec_col].sum().sort_values(ascending=False)
    top_m = by_m.head(10)
    rest_m = by_m.iloc[10:].sum()
    series_m = top_m.copy()
    other_m = f"All other medications ({max(len(by_m) - 10, 0):,})"
    if rest_m > 0:
        series_m[other_m] = rest_m
    base_m = by_m.sum() or 1
    panel("Which medications do patients write about most?",
          bars(series_m, lambda v: f"{int(v):,} · {v / base_m * 100:.1f}%", lead=top_m.index[0] if len(top_m) else None,
               pct_w=128, other=other_m, scale=series_m.max()),
          f"Volume is far flatter for medications than for conditions: the ten largest cover only {pct(top_m.sum() / base_m)} "
          f"of records, so no single medication dominates.", key="meds", delay=.08)

    unit = st.radio("Group by", ["Medications", "Conditions"], horizontal=True, label_visibility="collapsed")
    counts = by_m if unit == "Medications" else by_c
    edges = [(1, 1, "1"), (2, 5, "2 to 5"), (6, 10, "6 to 10"), (11, 50, "11 to 50"), (51, 100, "51 to 100"), (101, 500, "101 to 500"), (501, 10**9, "Over 500")]
    ent, rev = [], []
    for lo, hi, lab in edges:
        sel = counts[(counts >= lo) & (counts <= hi)]
        ent.append(len(sel))
        rev.append(sel.sum())
    te, tr = sum(ent) or 1, sum(rev) or 1

    def stack(vals, tot):
        parts = []
        for i, v in enumerate(vals):
            if not v:
                continue
            share = v / tot
            label = "" if share < .07 else f"{share * 100:.0f}%"
            if label and i == 0:
                label = f"<span class='lbl'>{label}</span>"
            cls = "dotfill" if i == 0 else ""
            colour = "#0B2545" if i < 3 else "#E0F7FA"
            parts.append(f"<div class='{cls}' style='width:{share * 100:.2f}%;background:{RAMP7[i]};color:{colour}' "
                         f"title='{edges[i][2]}: {share * 100:.1f}%'>{label}</div>")
        return "<div class='stack'>" + "".join(parts) + "</div>"
    small = ent[0] + ent[1]
    body = (f"<div class='label'>{unit}</div>{stack(ent, te)}<div style='height:12px'></div>"
            f"<div class='label'>Records they hold</div>{stack(rev, tr)}"
            + legend([(f"{e[2]} records", ".dotfill" if i == 0 else RAMP7[i]) for i, e in enumerate(edges)]))
    panel("How concentrated is the feedback?", body,
          f"{pct(small / te)} of {unit.lower()} hold five records or fewer, yet together they account for only "
          f"{pct((rev[0] + rev[1]) / tr)} of the data. Read one colour across both bars.",
          key="thinavg", delay=.16,
          lead=f"The upper bar divides the {unit.lower()} by how many records each holds; the lower bar divides the records across the same groups.")

if not has_records:
    st.info("This summary table has distinct reviews only. Run Notebook 3 Run 2 and copy its overview_cube.parquet to count every record.")
footer()
