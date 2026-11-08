"""Shared pieces for the dashboard pages: sidebar filters, calculations on the summary table, and HTML charts."""
import html

import numpy as np
import pandas as pd
import streamlit as st

from core import overview_cube, overview_meta, tip

BANDS = [(1, 2, "1 to 2"), (3, 5, "3 to 5"), (6, 10, "6 to 10"), (11, 30, "11 to 30"), (31, 100, "31 to 100"), (101, 10**9, "Over 100")]
RANK_MIN = 30
RAMP7 = ["#E0F7FA", "#B2EBF2", "#4DD0E1", "#00ACC1", "#1976D2", "#1565C0", "#0D47A1"]


def esc(s):
    return html.escape(str(s), quote=True)


def hero(eyebrow, title, lede):
    st.markdown(f"<div class='hero'><div class='eyebrow'>{eyebrow}</div><div class='title'>{title}</div>"
                f"<div class='lede'>{lede}</div></div>", unsafe_allow_html=True)


def not_recorded():
    return (overview_meta() or {}).get("not_recorded_label", "Condition not recorded")


# ---------------------------------------------------------------- filters
def filters(show_years=True):
    """Condition, Medication and Years in the sidebar; the choice carries across dashboard pages."""
    cube = overview_cube()
    if cube is None:
        st.error("data/overview_cube.parquet is missing. Copy it from derived/dashboard in the project Drive.")
        st.stop()
    ss = st.session_state
    nr = not_recorded()
    conds = sorted(c for c in cube["condition_label"].unique() if c != nr) + [nr]
    y0, y1 = int(cube["review_year"].min()), int(cube["review_year"].max())
    ss.setdefault("f_cond", "All conditions")
    ss.setdefault("f_med", "All medications")
    ss.setdefault("f_years", (y0, y1))
    with st.sidebar:
        st.markdown("<div class='side-h'>Filters</div>", unsafe_allow_html=True)
        opts = ["All conditions"] + conds
        cond = st.selectbox("Condition", opts, index=opts.index(ss.f_cond) if ss.f_cond in opts else 0)
        pool = cube if cond == "All conditions" else cube[cube["condition_label"] == cond]
        mopts = ["All medications"] + sorted(pool["drugName"].unique())
        med = st.selectbox("Medication", mopts, index=mopts.index(ss.f_med) if ss.f_med in mopts else 0)
        years = st.slider("Years", y0, y1, tuple(ss.f_years)) if show_years else (y0, y1)
        if st.button("Reset filters", width="stretch"):
            ss.f_cond, ss.f_med, ss.f_years = "All conditions", "All medications", (y0, y1)
            st.rerun()
    ss.f_cond, ss.f_med = cond, med
    if show_years:
        ss.f_years = years
    return cond, med, years


def scope_line(cond, med, years, n, noun="distinct reviews"):
    scope = ("all conditions" if cond == "All conditions" else cond) + ("" if med == "All medications" else f" · {med}")
    st.caption(f"{n:,} {noun} · {scope} · {years[0]} to {years[1]}")


@st.cache_data(show_spinner=False)
def view(cond, med, years):
    c = overview_cube()
    if cond != "All conditions":
        c = c[c["condition_label"] == cond]
    if med != "All medications":
        c = c[c["drugName"] == med]
    return c[c["review_year"].between(*years)]


def hist(c):
    return c.groupby("rating")["reviews"].sum().reindex(range(1, 11), fill_value=0)


def stats(h):
    n = int(h.sum())
    if not n:
        return {"n": 0}
    cum = h.cumsum()
    mean = float((h.index * h).sum() / n)
    sd = float(np.sqrt(((h.index - mean) ** 2 * h).sum() / n))
    return {"n": n, "mean": mean, "median": int(h.index[(cum >= n / 2).values][0]), "mode": int(h.idxmax()), "sd": sd,
            "r1": h[1] / n, "r10": h[10] / n, "low": h[1:3].sum() / n, "high": h[8:10].sum() / n}


@st.cache_data(show_spinner=False)
def group_table(cond, med, years, by):
    """One row per medication or condition: reviews, records, rating counts 1-10, mean, sd, shares."""
    c = view(cond, med, years)
    piv = c.pivot_table(index=by, columns="rating", values="reviews", aggfunc="sum", fill_value=0).reindex(columns=range(1, 11), fill_value=0)
    rec = c.groupby(by)["records"].sum() if "records" in c else c.groupby(by)["reviews"].sum()
    n = piv.sum(1)
    piv = piv[n > 0]
    n = n[n > 0]
    w = np.arange(1, 11)
    mean = (piv.values * w).sum(1) / n.values
    sd = np.sqrt((piv.values * (w - mean[:, None]) ** 2).sum(1) / n.values)
    cum = piv.cumsum(1).values
    median = np.argmax(cum >= (n.values[:, None] / 2), axis=1) + 1
    mode = piv.values.argmax(1) + 1
    t = pd.DataFrame({"reviews": n.values, "records": rec.reindex(piv.index).fillna(0).astype(int).values, "mean": mean, "sd": sd,
                      "median": median, "mode": mode, "r1": piv[1].values / n.values, "r10": piv[10].values / n.values,
                      "low": piv[[1, 2, 3]].sum(1).values / n.values, "high": piv[[8, 9, 10]].sum(1).values / n.values,
                      "dist": [list(map(int, r)) for r in piv.values]}, index=piv.index)
    t.index.name = by
    return t


# ---------------------------------------------------------------- HTML components
def kpis(items, n=None):
    from core import kpi
    n = n or len(items)
    return f"<div class='kpis' style='--n:{n}'>" + "".join(kpi(*it, delay=i * .06) for i, it in enumerate(items)) + "</div>"


def panel(question, body, note="", key=None, delay=0.0, lead=""):
    t = f" {tip(key)}" if key else ""
    lead_html = f"<div class='lead-in'>{lead}</div>" if lead else ""
    note_html = f"<div class='note'>{note}</div>" if note else ""
    st.markdown(f"<div class='card' style='--d:{delay:.2f}s'><div class='q'>Business question</div>"
                f"<div class='qt'>{question}{t}</div>{lead_html}{body}{note_html}</div>", unsafe_allow_html=True)


def bars(series, fmt, lead=None, label_w=190, pct_w=74, other=None, scale=None):
    top = scale or (series.max() if len(series) else 1) or 1
    rows = []
    for i, (name, v) in enumerate(series.items()):
        cls = "fill other" if name == other else ("fill lead" if name == lead else "fill")
        rows.append(f"<div class='bar' style='--lw:{label_w}px;--pw:{pct_w}px'><span class='name' title='{esc(name)}'>{esc(name)}</span>"
                    f"<div class='track'><div class='{cls}' style='width:{min(v / top, 1) * 100:.1f}%;--d:{0.15 + i * 0.04:.2f}s'></div></div>"
                    f"<span class='pct'>{fmt(v)}</span></div>")
    return "".join(rows)


def columns(values, labels, fmt, dark=(), soft=(), sub=None, height=190, marks=(), hatch=()):
    vmax = max([v for v in values if pd.notna(v)] or [1]) or 1
    cols = "".join(
        (f"<div class='col'><div class='v'>{fmt(v)}</div><div class='c{' dark' if i in dark else (' soft' if i in soft else (' hatch' if i in hatch else ''))}' "
         f"style='height:{v / vmax * 82:.1f}%;--d:{0.15 + i * 0.04:.2f}s'></div></div>") if pd.notna(v)
        else "<div class='col'><div class='v'>-</div></div>" for i, v in enumerate(values))
    mk = "".join(f"<div class='mark' style='left:{pos:.2f}%'><span>{esc(lab)}</span></div>" for pos, lab in marks)
    xl = "".join(f"<div><b>{esc(l)}</b>{'' if sub is None else sub[i]}</div>" for i, l in enumerate(labels))
    return f"<div class='cols' style='--h:{height}px'>{mk}{cols}</div><div class='colx'>{xl}</div>"


def legend(items):
    # A colour, or a texture class name starting with "." (".hatch", ".hatch-light", ".dotfill").
    sw = lambda c: f"<i class='{c[1:]}'></i>" if c.startswith(".") else f"<i style='background:{c}'></i>"
    return "<div class='legend'>" + "".join(f"<span>{sw(c)}{esc(l)}</span>" for l, c in items) + "</div>"


def empty(text):
    return f"<div class='empty'><span>{esc(text)}</span></div>"


def pct(v, d=1):
    return "-" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v * 100:.{d}f}%"
