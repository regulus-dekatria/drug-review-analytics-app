"""Shared pieces for the dashboard pages: sidebar filters, calculations on the summary table, and HTML charts."""
import html
from contextlib import contextmanager

import numpy as np
import pandas as pd
import streamlit as st

from core import overview_cube, overview_meta, tip

BANDS = [(1, 2, "1 to 2"), (3, 5, "3 to 5"), (6, 10, "6 to 10"), (11, 30, "11 to 30"), (31, 100, "31 to 100"), (101, 10**9, "Over 100")]
RANK_MIN = 30
RAMP7 = ["#E0F7FA", "#B2EBF2", "#4DD0E1", "#00ACC1", "#1976D2", "#1565C0", "#0D47A1"]


def esc(s):
    return html.escape(str(s), quote=True)


def hero(title):
    st.markdown(f"<div class='hero'><div class='title'>{esc(title)}</div></div>", unsafe_allow_html=True)


def title_case(label):
    # "pill · birth · control" -> "Pill · Birth · Control"; keeps apostrophes intact, unlike str.title().
    minor = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "with"}
    words = str(label).split(" ")
    return " ".join(w if (i and w.lower() in minor) else w[:1].upper() + w[1:] for i, w in enumerate(words))


def controls(key):
    """A compact row of page controls, left-aligned, each as wide as its content."""
    return st.container(horizontal=True, key=f"ctl-{key}", vertical_alignment="bottom", gap="medium")


def not_recorded():
    return (overview_meta() or {}).get("not_recorded_label", "Condition not recorded")


# ---------------------------------------------------------------- filters
YEAR_PRESETS = {"All time": None, "2008 to 2012": (2008, 2012), "2013 to 2017": (2013, 2017), "2016 to 2017": (2016, 2017)}


def filters(show_years=True, show_ratings=True):
    """Condition, Medication, Ratings and Years in the sidebar, carried across pages; active filters show as chips.
    Each widget is bound to its own session key (f_cond, f_med, f_ratings, f_years), and every change from outside
    the widget (chips, reset, presets, table clicks) happens in a callback, before the widgets are drawn."""
    cube = overview_cube()
    if cube is None:
        st.error("data/overview_cube.parquet is missing. Copy it from derived/dashboard in the project Drive.")
        st.stop()
    ss = st.session_state
    nr = not_recorded()
    conds = ["All conditions"] + sorted(c for c in cube["condition_label"].unique() if c != nr) + [nr]
    y0, y1 = int(cube["review_year"].min()), int(cube["review_year"].max())
    defaults = {"f_cond": "All conditions", "f_med": "All medications", "f_years": (y0, y1), "f_ratings": []}
    for k, v in defaults.items():
        ss.setdefault(k, v)
    if ss.f_cond not in conds:
        ss.f_cond = "All conditions"
    pool = cube if ss.f_cond == "All conditions" else cube[cube["condition_label"] == ss.f_cond]
    meds = ["All medications"] + sorted(pool["drugName"].unique())
    if ss.f_med not in meds:
        ss.f_med = "All medications"
    ss.f_years = tuple(ss.f_years)

    def clear(k):
        ss[k] = defaults[k]
        if k == "f_cond":
            ss.f_med = "All medications"

    def reset():
        for k, v in defaults.items():
            ss[k] = v

    def preset():
        v = YEAR_PRESETS.get(ss.get("f_preset"))
        ss.f_years = v or (y0, y1)

    def cond_changed():
        ss.f_med = "All medications"

    with st.sidebar:
        st.markdown("<div class='side-h'>Filters</div>", unsafe_allow_html=True)
        chips = []
        if ss.f_cond != "All conditions":
            chips.append((ss.f_cond, "f_cond"))
        if ss.f_med != "All medications":
            chips.append((ss.f_med, "f_med"))
        if ss.f_ratings and show_ratings:
            chips.append(("rated " + ", ".join(map(str, sorted(ss.f_ratings))), "f_ratings"))
        if show_years and ss.f_years != (y0, y1):
            chips.append((f"{ss.f_years[0]} to {ss.f_years[1]}", "f_years"))
        if chips:
            with st.container(horizontal=True, key="ctl-chips", gap="small"):
                for label, k in chips:
                    st.button(f"{label}  ×", key=f"chip-{k}", help="Remove this filter", type="tertiary", on_click=clear, args=(k,))
                st.button("Reset all", key="chip-reset", on_click=reset, type="tertiary")
        st.selectbox("Condition", conds, key="f_cond", on_change=cond_changed)
        st.selectbox("Medication", meds, key="f_med")
        if show_ratings:
            st.pills("Ratings", list(range(1, 11)), selection_mode="multi", key="f_ratings",
                     help="Keep only reviews with these scores. Leave empty for every score.")
        if show_years:
            ss.f_preset = next((k for k, v in YEAR_PRESETS.items() if (v or (y0, y1)) == ss.f_years), None)
            st.segmented_control("Years", list(YEAR_PRESETS), key="f_preset", on_change=preset)
            st.slider("Year range", y0, y1, key="f_years", label_visibility="collapsed")
    ratings = tuple(sorted(ss.f_ratings or [])) if show_ratings else ()
    years = tuple(ss.f_years) if show_years else (y0, y1)
    return ss.f_cond, ss.f_med, years, ratings


@st.cache_data(show_spinner=False)
def view(cond, med, years, ratings=()):
    c = overview_cube()
    if cond != "All conditions":
        c = c[c["condition_label"] == cond]
    if med != "All medications":
        c = c[c["drugName"] == med]
    c = c[c["review_year"].between(*years)]
    if ratings:
        c = c[c["rating"].isin(ratings)]
    return c


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
def group_table(cond, med, years, by, ratings=()):
    """One row per medication or condition: reviews, records, rating counts 1-10, mean, sd, shares."""
    c = view(cond, med, years, ratings)
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


def card(title, body, note="", key=None, delay=0.0, lead=""):
    """One panel as HTML: heading (with tooltip), optional reading guide, the chart, and a note pinned to the bottom."""
    t = f" {tip(key)}" if key else ""
    lead_html = f"<div class='lead-in'>{lead}</div>" if lead else ""
    note_html = f"<div class='note'>{note}</div>" if note else ""
    return (f"<div class='card' style='--d:{delay:.2f}s'><div class='qt'>{title}{t}</div>"
            f"<div class='body'>{lead_html}{body}</div>{note_html}</div>")


def panel(title, body, note="", key=None, delay=0.0, lead=""):
    st.markdown(card(title, body, note, key, delay, lead), unsafe_allow_html=True)


def row(*cards):
    """Panels side by side in one grid row, so they share the same height and their notes line up."""
    st.markdown(f"<div class='row' style='--n:{len(cards)}'>" + "".join(cards) + "</div>", unsafe_allow_html=True)


def note(text):
    st.markdown(f"<div class='note'>{text}</div>", unsafe_allow_html=True)


def bars(series, fmt, lead=None, label_w=190, pct_w=74, other=None, scale=None, tall=False, colour=None, tips=None):
    top = scale or (series.max() if len(series) else 1) or 1
    rows = []
    for i, (name, v) in enumerate(series.items()):
        cls = "fill other" if name == other else ("fill lead" if name == lead else "fill")
        t = (tips or {}).get(name) or f"{name}: {fmt(v)}"
        bg = f";background:{colour}" if colour and cls == "fill" else ""
        rows.append(f"<div class='bar{' tall' if tall else ''}' style='--lw:{label_w}px;--pw:{pct_w}px' data-tip='{esc(t)}'><span class='name'>{esc(name)}</span>"
                    f"<div class='track'><div class='{cls}' style='width:{min(v / top, 1) * 100:.1f}%;--d:{0.15 + i * 0.04:.2f}s{bg}'></div></div>"
                    f"<span class='pct'>{fmt(v)}</span></div>")
    return "".join(rows)


def columns(values, labels, fmt, dark=(), soft=(), sub=None, height=190, marks=(), hatch=()):
    vmax = max([v for v in values if pd.notna(v)] or [1]) or 1
    cols = "".join(
        (f"<div class='col'><div class='v'>{fmt(v)}</div><div class='c{' dark' if i in dark else (' soft' if i in soft else (' hatch' if i in hatch else ''))}' "
         f"style='height:{v / vmax * 82:.1f}%;--d:{0.15 + i * 0.04:.2f}s'></div></div>") if pd.notna(v)
        else "<div class='col'><div class='v'>-</div></div>" for i, v in enumerate(values))
    mk = "".join(f"<div class='mark {m[2] if len(m) > 2 else ''}' style='left:{m[0]:.2f}%'><span>{esc(m[1])}</span></div>" for m in marks)
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


# ---------------------------------------------------------------- panels that hold controls
@contextmanager
def box(title, name, key=None, lead="", tools=None):
    """A panel card. Controls, when given, sit in the header on the right, the same way on every page.
    `tools` is a function that draws the controls and returns their values; the context yields those values."""
    t = f" {tip(key)}" if key else ""
    with st.container(key=f"card-{name}"):
        vals = None
        if tools:
            with st.container(horizontal=True, vertical_alignment="center", key=f"hd-{name}", gap="small"):
                st.markdown(f"<div class='qt'>{title}{t}</div>", unsafe_allow_html=True, width="stretch")
                vals = tools()
        else:
            st.markdown(f"<div class='qt'>{title}{t}</div>", unsafe_allow_html=True)
        if lead:
            st.markdown(f"<div class='lead-in'>{lead}</div>", unsafe_allow_html=True)
        yield vals


def show(body):
    st.markdown(body, unsafe_allow_html=True)


def pair(gap="medium"):
    """Two columns whose panels share one height (see the CSS for [data-testid=stColumn])."""
    return st.columns(2, gap=gap)


# Controls, all drawn the same way: label hidden, compact, inside the panel header.
def find(key, placeholder):
    return st.text_input(placeholder, key=key, placeholder=placeholder, label_visibility="collapsed", width=180)


def choose(key, options, default=None, fmt=None, label="Choose"):
    v = st.segmented_control(label, options, default=default if default is not None else options[0], key=key,
                             label_visibility="collapsed", format_func=fmt)
    return v if v is not None else (default if default is not None else options[0])


def pick(key, options, default=0, fmt=str, label="Choose", width=180):
    return st.selectbox(label, options, index=default, key=key, label_visibility="collapsed", format_func=fmt, width=width)


MINS = [30, 100, 1]
min_fmt = lambda v: "Any number" if v in (1, 2) else f"{v}+ reviews"


# ---------------------------------------------------------------- charts from the old dashboard
def diverge(rows, label_w=200, right_label=True, legend_items=None, scroll=None):
    """Centred bars: the low share reaches left of the centre line, the high share right, the middle straddles it.
    rows: (name, low, high, tooltip). Shares are 0 to 1."""
    out = []
    for i, (name, lo, hi, tipt) in enumerate(rows):
        mid = max(0.0, 1 - lo - hi)
        left = 50 - (lo + mid / 2) * 50
        out.append(f"<div class='dv' style='--lw:{label_w}px' data-tip='{esc(tipt)}'><span class='name'>{esc(name)}</span>"
                   f"<div class='dvt'><i class='axis'></i>"
                   f"<b class='lo' style='left:{left:.2f}%;width:{lo * 50:.2f}%'></b>"
                   f"<b class='md' style='left:{left + lo * 50:.2f}%;width:{mid * 50:.2f}%'></b>"
                   f"<b class='hi' style='left:{left + (lo + mid) * 50:.2f}%;width:{hi * 50:.2f}%'>"
                   f"{f'<em>{hi * 100:.1f}%</em>' if right_label and hi >= .08 else ''}</b></div></div>")
    body = "".join(out) or empty("Nothing matches.")
    head = "<div class='dvhead'><span>rated lower</span><span>rated higher</span></div>"
    inner = head + body
    if scroll:
        inner = f"<div class='scroll' style='max-height:{scroll}px'>{inner}</div>"
    return inner + (legend(legend_items) if legend_items else "")


def dots(rows, vmax=4.5, label_w=190, scroll=None, ticks=(0, 1, 2, 3, 4)):
    """Dot plot on one axis from zero: rows (name, value, tooltip)."""
    axis = "".join(f"<span style='left:{t / vmax * 100:.2f}%'>{t}</span>" for t in ticks)
    grid = "".join(f"<i style='left:{t / vmax * 100:.2f}%'></i>" for t in ticks)
    out = "".join(f"<div class='dt' style='--lw:{label_w}px' data-tip='{esc(tp)}'><span class='name'>{esc(n)}</span>"
                  f"<div class='dtt'>{grid}<b style='left:{min(v / vmax, 1) * 100:.2f}%'></b></div><span class='pct'>{v:.2f}</span></div>"
                  for n, v, tp in rows) or empty("Nothing matches.")
    top = f"<div class='dt dtaxis' style='--lw:{label_w}px'><span class='name'></span><div class='dtt'>{axis}</div><span class='pct'></span></div>"
    inner = f"<div class='scroll' style='max-height:{scroll}px'>{out}</div>" if scroll else out
    return top + inner


def ladder9(means, lo_pad=.35):
    """What score it takes at each tenth of the ranking: nine rungs, labels alternating above and below."""
    steps = [(10, "bottom 10%"), (20, "bottom 20%"), (30, "bottom 30%"), (40, "bottom 40%"), (50, "middle"),
             (60, "top 40%"), (70, "top 30%"), (80, "top 20%"), (90, "top 10%")]
    vals = [float(np.quantile(means, p / 100)) for p, _ in steps]
    lo, hi = vals[0] - lo_pad, vals[-1] + lo_pad
    # Labels alternate above and below the line; where rungs crowd, a third row keeps them apart.
    xs = [(v - lo) / (hi - lo) * 100 for v in vals]
    rows, last = [], {}
    for i, x in enumerate(xs):
        lane = 2 if i == 4 else (1 if i % 2 else 0)  # the middle rung always sits lowest, so it never collides
        if lane != 2 and lane in last and x - last[lane] < 13:
            lane += 2
        last[lane] = x
        rows.append(lane)
    rungs = "".join(f"<div class='rung{' strong' if p == 50 else ''} lane{lane}' style='left:{x:.1f}%'><i></i>"
                    f"<b>{v:.2f}</b><small>{lab}</small></div>" for (p, lab), v, x, lane in zip(steps, vals, xs, rows))
    return vals, (f"<div class='ladder' style='margin:100px 10px 10px'>{rungs}</div>"
                  f"<div class='label' style='text-align:center;margin-top:60px'>average rating of a medication</div>")


def table(df, key, pick_col=None, target=None, **kw):
    """A table; when pick_col and target are given, clicking a row filters the dashboard to that condition or medication."""
    if not pick_col:
        return st.dataframe(df, hide_index=True, width="stretch", **kw)
    ss = st.session_state
    gen = ss.get(f"{key}_gen", 0)
    wkey = f"{key}_{gen}"

    def chosen():
        rows = ss[wkey].selection.rows
        if rows:
            ss[target] = df.iloc[rows[0]][pick_col]
            if target == "f_cond":
                ss.f_med = "All medications"
            ss[f"{key}_gen"] = gen + 1  # a fresh table, so the selection does not stick after the filter is removed
    st.dataframe(df, hide_index=True, width="stretch", key=wkey, on_select=chosen, selection_mode="single-row", **kw)
