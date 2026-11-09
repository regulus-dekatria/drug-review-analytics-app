"""Volume Analysis: the old dashboard's four panels, with the Chart/Table and Medications/Conditions toggles."""
import pandas as pd
import streamlit as st

from dash import (RAMP7, bars, box, choose, columns, filters, hero, hist, kpis, legend, not_recorded, note, pair, pct, show,
                  view)

hero("Volume Analysis")
f = filters()
c = view(*f)
if c["reviews"].sum() == 0:
    st.warning("No reviews match these filters.")
    st.stop()
rec_col = "records" if "records" in c.columns else "reviews"
n_rev, n_rec = int(c["reviews"].sum()), int(c[rec_col].sum())
votes = int(c["helpful_votes_records"].sum()) if "helpful_votes_records" in c else int(c["helpful_votes"].sum())
nr = not_recorded()
show(kpis([
    ("Records", f"{n_rec:,}", "every listing, including brand and generic copies", "records", "database"),
    ("Reviews", f"{n_rev:,}", "one per patient", "reviews", "forum"),
    ("Medications", f"{c['drugName'].nunique():,}", "brand and generic counted separately", "meds", "medication"),
    ("Conditions", f"{c.loc[c['condition_label'] != nr, 'condition_label'].nunique():,}", "named conditions", "conds", "stethoscope"),
    ("Helpful Votes", f"{votes:,}", f"{votes / max(n_rec, 1):.1f} per record on average", "avgvotes", "thumb_up")], n=5))


def top_with_other(counts, noun):
    top = counts.head(10)
    series = top.copy()
    label = f"All other {noun} ({max(len(counts) - 10, 0):,})"
    if counts.iloc[10:].sum() > 0:
        series[label] = counts.iloc[10:].sum()
    return top, series, label


by_c = c[c["condition_label"] != nr].groupby("condition_label")[rec_col].sum().sort_values(ascending=False)
by_m = c.groupby("drugName")[rec_col].sum().sort_values(ascending=False)
top_c, ser_c, oth_c = top_with_other(by_c, "conditions")
top_m, ser_m, oth_m = top_with_other(by_m, "medications")
base_c, base_m = by_c.sum() or 1, by_m.sum() or 1

# The rating distribution ignores the rating filter, so every score stays visible; chosen scores are drawn darker.
h = hist(view(f[0], f[1], f[2], ()))
share = h / (h.sum() or 1)
chosen = [r - 1 for r in f[3]] if f[3] else [0, 9]
l, r = pair()
with l:
    with box("Rating Distribution", "vol-dist", key="polar", tools=lambda: choose("vol_view", ["Chart", "Table"], label="View"),
             lead="Reviews at each score." + (" Scores kept by the Ratings filter are darker." if f[3] else " The two ends are darker because that is where reviews collect.")) as mode:
        if mode == "Table":
            st.dataframe(pd.DataFrame({"Rating": range(1, 11), "Reviews": h.values, "Share": (share.values * 100)}), hide_index=True, width="stretch",
                         height=388, column_config={"Reviews": st.column_config.NumberColumn(format="localized"),
                                                    "Share": st.column_config.ProgressColumn(min_value=0.0, max_value=100.0, format="%.1f%%")})
        else:
            show(columns(list(h.values), [str(i) for i in range(1, 11)], lambda v: f"{v:,}", dark=tuple(chosen), sub=[f"{x * 100:.1f}%" for x in share], height=250))
        note(f"{pct(share[1] + share[10])} of patients gave a 1 or a 10, and few chose the middle. People mostly write a review when they "
             f"are delighted or disappointed.")
with r:
    with box("Top 10 Conditions by Volume", "vol-conds", key="conds", lead="Records for the ten largest conditions; the striped bar holds every other condition."):
        show(bars(ser_c, lambda v: f"{int(v):,} · {v / base_c * 100:.1f}%", lead=top_c.index[0] if len(top_c) else None, pct_w=128, other=oth_c)
             + legend([("largest", "var(--navy)"), ("next nine", "var(--blue)"), ("every other condition combined", ".hatch-light")]))
        note(f"The ten largest conditions hold {pct(top_c.sum() / base_c)} of all records. Stock and staffing questions for these conditions "
             f"have the most patient feedback behind them.")

BANDS7 = [(1, 1, "1"), (2, 2, "2"), (3, 5, "3-5"), (6, 10, "6-10"), (11, 30, "11-30"), (31, 100, "31-100"), (101, 10**9, "100+")]


def stack(vals):
    tot = sum(vals) or 1
    parts = []
    for i, v in enumerate(vals):
        if not v:
            continue
        sh = v / tot
        lab = f"{sh * 100:.1f}%" if sh >= .06 else ""
        colour = "#0B2545" if i < 3 else "#E0F7FA"
        parts.append(f"<div style='width:{sh * 100:.2f}%;background:{RAMP7[i]};color:{colour}' data-tip='{BANDS7[i][2]} records&#10;{v:,} · {sh * 100:.1f}%'>{lab}</div>")
    return "<div class='stack' style='height:44px'>" + "".join(parts) + "</div>"


l, r = pair()
with l:
    with box("Top 10 Medications by Volume", "vol-meds", key="meds", lead="Records for the ten largest medications; the striped bar holds every other medication."):
        show(bars(ser_m, lambda v: f"{int(v):,} · {v / base_m * 100:.1f}%", lead=top_m.index[0] if len(top_m) else None, pct_w=128, other=oth_m)
             + legend([("largest", "var(--navy)"), ("next nine", "var(--blue)"), ("every other medication combined", ".hatch-light")]))
        note(f"Feedback is spread far more evenly across medications: the ten largest hold only {pct(top_m.sum() / base_m)} of records, "
             f"so no single product dominates.")
with r:
    with box("Volume Concentration", "vol-conc", key="thinavg", tools=lambda: choose("vol_band", ["Medications", "Conditions"], label="Group"),
             lead="The upper bar splits medications or conditions by how many records each holds; the lower bar shows the records those groups hold.") as unit:
        counts = by_m if unit == "Medications" else by_c
        ent = [int(((counts >= lo) & (counts <= hi)).sum()) for lo, hi, _ in BANDS7]
        rev = [int(counts[(counts >= lo) & (counts <= hi)].sum()) for lo, hi, _ in BANDS7]
        show("<div class='legend' style='margin:0 0 14px'><span style='text-transform:uppercase;letter-spacing:.08em;font-size:.74rem'>records held</span>"
             + "".join(f"<span><i style='background:{RAMP7[i]}'></i>{b[2]}</span>" for i, b in enumerate(BANDS7)) + "</div>"
             f"<div class='bandrow'><span>{unit}</span>{stack(ent)}</div><div style='height:12px'></div>"
             f"<div class='bandrow'><span>Records</span>{stack(rev)}</div>")
        small = sum(ent[:3]) / (sum(ent) or 1)
        note(f"{pct(small)} of {unit.lower()} hold five records or fewer, yet together they account for only "
             f"{pct(sum(rev[:3]) / (sum(rev) or 1))} of the feedback. Read one colour across both bars.")
