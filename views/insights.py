"""Reviews Analysis: what patients write about, from the review text."""
import pandas as pd
import streamlit as st

from core import reviews_analysis
from dash import bars, card, controls, empty, esc, hero, kpis, legend, row, title_case

hero("Reviews Analysis")
ra = reviews_analysis()
if ra is None:
    st.error("data/reviews_analysis.json is missing.")
    st.stop()

views = list(ra["views"].keys())
pick = st.session_state.get("f_cond", "All conditions")
with controls("insights"):
    view = st.selectbox("Condition", views, index=views.index(pick) if pick in views else 0, width=260, label_visibility="collapsed",
                        help="The ten conditions with the most reviews have their own analysis.")
v = ra["views"][view]
sent = v["sentiment"]
neutral = sent.get("neutral", max(0.0, 100 - sent["positive"] - sent["negative"]))

st.markdown(kpis([
    ("Reviews", f"{v['reviews']:,}", "one per patient", "reviews", "forum"),
    ("Positive Wording", f"{sent['positive']:.1f}%", "reviews that read as positive", "sentiment", "sentiment_satisfied"),
    ("Neutral Wording", f"{neutral:.1f}%", "reviews that read as neither", "sentiment", "sentiment_neutral"),
    ("Negative Wording", f"{sent['negative']:.1f}%", "reviews that read as negative", "sentiment", "sentiment_dissatisfied"),
    ("Wording Matches Rating", f"{v['words_vs_score']['agreement']:.1f}%", "tone agrees with the star rating", "vader_agree", "rule")], n=5),
    unsafe_allow_html=True)

wl = pd.Series(v["watchlist"]).sort_values(ascending=False)
th = pd.DataFrame(v["themes"]).head(10)


def theme_name(t):
    """Theme models name a group by its top words, singular and plural included; keep the first of each pair."""
    seen, keep = set(), []
    for w in str(t).split(" · "):
        stem = w.lower().rstrip("s")
        if stem and stem not in seen:
            seen.add(stem)
            keep.append(w)
    return title_case(" · ".join(keep))


th_series = pd.Series(th["share"].values, index=[theme_name(t) for t in th["theme"]]) if len(th) else pd.Series(dtype=float)
th_series = th_series.groupby(level=0, sort=False).sum()
wl_t = pd.Series(wl.values, index=[title_case(k) for k in wl.index])
fmt = lambda x: f"{x:.1f}%"
top_topic = wl_t.index[0] if len(wl_t) else ""
topic_note = (f"The most mentioned topic, {top_topic}, appears in {wl_t.iloc[0]:.1f}% of reviews"
              + (f", {wl_t.iloc[0] / wl_t.iloc[1]:.1f} times as often as {wl_t.index[1]}" if len(wl_t) > 1 and wl_t.iloc[1] else "")
              + f". {v['other_medication_named']:.1f}% of reviews also name another medication."
              if len(wl) else "")
theme_note = (f"The largest theme, {th_series.index[0]}, covers {th_series.iloc[0]:.1f}% of reviews. Use themes to see what "
              f"patients talk about together; {v['unassigned']:.1f}% of reviews fit no theme." if len(th_series) else "")
row(card("Topics Mentioned", bars(wl_t, fmt, lead=top_topic, label_w=210) + legend([("most mentioned", "var(--navy)"), ("other topics", "var(--blue)")]),
         topic_note, key="watchlist", delay=.05, lead="Share of reviews that mention each topic. A review can mention several."),
    card("Review Themes",
         (bars(th_series, fmt, label_w=250, lead=th_series.index[0]) if len(th_series) else empty("No themes for this view."))
         + legend([("largest theme", "var(--navy)"), ("other themes", "var(--blue)")]),
         theme_note, key="themes", delay=.1, lead="Groups of reviews that talk about the same things, named by their most typical words."))

def cloud(words, side):
    """Words sized by rank, set line by line: each line has its largest word in the centre, sizes falling toward both edges."""
    n = len(words)
    if not n:
        return empty("No words for this view.")
    size = lambda i: 2.3 - i * (1.35 / max(n - 1, 1))
    lines = 2 if n <= 12 else 3
    out = []
    for li in range(lines):
        ranks = list(range(li, n, lines))  # this line's words, strongest first
        left, right = ranks[1::2][::-1], ranks[2::2]
        order = left + ranks[:1] + right
        spans = "".join(f"<span style='font-size:{size(i):.2f}rem;font-weight:{700 if i < 3 else 500}' data-tip='rank {i + 1} of {n}'>{esc(words[i])}</span>"
                        for i in order)
        out.append(f"<div class='cline'>{spans}</div>")
    return f"<div class='cloud {side}'>{''.join(out)}</div>"


row(card("Words in Low and High Ratings",
         f"<div class='split'><div><div class='sublabel'>Typical of low ratings</div>{cloud(v['words_low'], 'low')}</div>"
         f"<div><div class='sublabel'>Typical of high ratings</div>{cloud(v['words_high'], 'high')}</div></div>",
         "Words on the left signal a complaint. New messages that use them are worth reading first.", key="words", delay=.14,
         lead="The words that most clearly separate reviews rated 1 to 3 from reviews rated 8 to 10. Larger words rank higher."))

# Terms caught after a negation ("no relief") are shown with it, so a positive word never looks like a complaint.
NEGATED = {"relief": "no relief", "helped": "not helped", "help": "no help", "helps": "doesn't help", "works": "doesn't work",
           "worked": "didn't work", "effective": "not effective", "working": "not working"}
NEG_WORDS = ("not", "n't", "no ", "never", "stopped", "waste", "useless")
terms = v.get("watchlist_top_terms", {})


def label(term, cat):
    if "did not work" in cat.lower() and not any(nw in term.lower() for nw in NEG_WORDS):
        return NEGATED.get(term.lower(), f"{term} (after no or not)")
    return term


body = ""
for cat in wl.index:
    tt = terms.get(cat) or []
    if not tt:
        continue
    top_n = tt[0]["reviews"] or 1
    cells = "".join(f"<td><div class='t'>{esc(label(t['term'], cat))}</div><div class='n'>{t['reviews']:,}</div>"
                    f"<div class='track'><div class='fill{' lead' if j == 0 else ''}' style='width:{max(4, t['reviews'] / top_n * 100):.0f}%'></div></div></td>"
                    for j, t in enumerate(tt[:5]))
    cells += "<td></td>" * (5 - min(len(tt), 5))
    body += f"<tr><th scope='row'>{esc(title_case(cat))}</th>{cells}</tr>"
table = (f"<table class='terms'><thead><tr><th>Topic</th><th colspan='5'>Terms, Most Used First</th></tr></thead><tbody>{body}</tbody></table>"
         + legend([("most used term in the topic", "var(--navy)"), ("bar length: reviews, against the topic's most used term", "var(--blue)")])
         if body else empty("No terms for this view."))
top_cat = next((c for c in wl.index if terms.get(c)), None)
terms_note = (f"In {title_case(top_cat) if top_cat else ''}, \"{label(terms[top_cat][0]['term'], top_cat)}\" leads with {terms[top_cat][0]['reviews']:,} reviews. "
              f"These are the exact words patients use, so they make good search terms when reading the reviews themselves."
              if top_cat else "")
row(card("Most Mentioned Terms", table, terms_note, key="watchlist", delay=.18,
         lead="The five words or phrases patients use most for each topic, with the number of reviews."))
