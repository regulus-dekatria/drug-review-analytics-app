"""Reviews Analysis results from the NLP notebook: sentiment, watchlist, themes and words."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import AQUA, BLUE, CYAN, ICE, INK, MUTED, NAVY, footer, reviews_analysis

from dash import hero
hero("Dashboard · Reviews Analysis", "What patients write about",
     "Natural language processing on the review text itself: sentiment, a keyword watchlist, semantic themes and the words that "
     "separate low ratings from high ones, measured on the distinct reviews from 2008 to 2017.")

ra = reviews_analysis()
if ra is None:
    st.error("data/reviews_analysis.json is missing. Copy it from derived/nlp in the project Drive.")
    st.stop()


def hbar(labels, values, colour=BLUE, suffix="%"):
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=colour,
                           text=[f"{v:.1f}{suffix}" for v in values], textposition="outside", cliponaxis=False))
    fig.update_layout(height=40 * len(labels) + 60, margin=dict(l=10, r=40, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="IBM Plex Sans", color=INK),
                      xaxis=dict(showgrid=False, visible=False), yaxis=dict(autorange="reversed"))
    return fig


views = list(ra["views"].keys())
pick = st.session_state.get("f_cond", "All conditions")
view = st.selectbox("Condition (the ten largest have their own analysis)", views, index=views.index(pick) if pick in views else 0)
v = ra["views"][view]
st.caption(f"{v['reviews']:,} reviews in this view · source: {ra['basis']} · NLP run {ra.get('run', '?')}")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Reviews", f"{v['reviews']:,}")
k2.metric("Positive wording", f"{v['sentiment']['positive']:.1f}%")
k3.metric("Negative wording", f"{v['sentiment']['negative']:.1f}%")
k4.metric("Wording agrees with stars", f"{v['words_vs_score']['agreement']:.1f}%",
          help="Share of reviews where VADER's mood label matches the reviewer's rating group.")

left, right = st.columns(2)
with left:
    st.subheader("How often do patients raise each topic?")
    wl = v["watchlist"]
    st.plotly_chart(hbar(list(wl.keys()), list(wl.values()), NAVY), width="stretch", config={"displayModeBar": False})
    st.caption(f"Share of reviews mentioning each watchlist category; a review can count in several. "
               f"{v['other_medication_named']:.1f}% name another medication (context, not a category).")
    with st.expander("Most mentioned terms per category"):
        for cat, terms in v["watchlist_top_terms"].items():
            st.write(f"**{cat}:** " + ", ".join(f"{t['term']} ({t['reviews']:,})" for t in terms))
with right:
    st.subheader("What themes do reviews fall into?")
    th = pd.DataFrame(v["themes"]).head(10)
    if len(th):
        st.plotly_chart(hbar(th["theme"].tolist(), th["share"].tolist(), CYAN), width="stretch", config={"displayModeBar": False})
    st.caption(f"{len(th)} largest themes ({v['themes_scope']}), labelled by their most typical words. "
               f"Unassigned: {v['unassigned']:.1f}% of reviews.")

st.subheader("Which words separate low ratings from high ratings?")
c1, c2 = st.columns(2)
c1.markdown("**Typical of low ratings**<br>" + "".join(f"<span class='chip'>{w}</span>" for w in v["words_low"]), unsafe_allow_html=True)
c2.markdown("**Typical of high ratings**<br>" + "".join(f"<span class='chip'>{w}</span>" for w in v["words_high"]), unsafe_allow_html=True)

with st.expander("How these figures were checked"):
    val = ra.get("validation", {})
    st.write(f"- Sentiment (VADER) agrees with the reviewer's rating group on {val.get('vader_accuracy', 0):.1f}% of reviews "
             f"(Cohen's kappa {val.get('vader_kappa', 0):.3f}).")
    st.write(f"- Themes: coherence (NPMI) {val.get('theme_coherence', 0):.3f}, stability across seeds (ARI) {val.get('theme_stability', 0):.3f}.")
    st.write(f"- {val.get('symptom_mentions_negated', 0):.1f}% of symptom mentions follow a negation word (\"no nausea\").")

footer()
