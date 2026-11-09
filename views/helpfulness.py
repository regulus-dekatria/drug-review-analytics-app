"""Predict whether a new review will be among the most helpful of its month."""
import streamlit as st

from core import categories, helpfulness, models_ready, preprocessing
from dash import card, hero, row

hero("Predict Helpfulness")

if not models_ready():
    st.stop()

cats = categories()
with st.form("help"):
    text = st.text_area("Review", height=140, max_chars=3000,
                        help="Estimates the chance that readers will rank this review among the most helpful quarter of reviews posted in the same month.")
    c1, c2, c3 = st.columns([1, 1.4, 1.4])
    rating = c1.slider("Star rating", 1, 10, 8)
    condition = c2.selectbox("Condition", ["Unknown"] + [c for c in cats["conditions"] if c != "Unknown"],
                             help="Type to search. Conditions the model never saw count as Unknown.")
    medication = c3.selectbox("Medication", ["Unknown"] + [m for m in cats["medications"] if m != "Unknown"],
                              help="Type to search. Medications first reviewed after 2015 count as Unknown.")
    go = st.form_submit_button("Predict", type="primary")

if go:
    if not text.strip():
        st.warning("Type or paste a review first.")
    else:
        score, cond, med = helpfulness(text, rating, condition, medication)
        q = {float(k): v for k, v in (preprocessing().get("objective2_test_score_quantiles") or {}).items()}
        if q and score >= q.get(0.9, 1):
            band = "in the top 10% of recent reviews"
        elif q and score >= q.get(0.75, 1):
            band = "in the top 25% of recent reviews"
        elif q and score >= q.get(0.5, 1):
            band = "above the middle of recent reviews"
        else:
            band = "below the middle of recent reviews"
        verdict = "Likely helpful" if q and score >= q.get(0.75, 1) else "Not likely in the top 25%"
        row(card("Helpfulness Estimate",
                 f"<div class='big'>{verdict}</div><div class='label'>{len(text.split())} words · rating {rating} · {cond} · {med}</div>",
                 "About one review in four reaches the most helpful quarter of its month, so 25% is the chance to beat.", key="auc", delay=.02),
            card("Chance of Being Among the Most Helpful",
                 f"<div class='big'>{score * 100:.0f}%</div><div class='label'>scores {band}</div>",
                 "Popular medications' pages get more readers, so part of this score reflects how many people will see the review, "
                 "not only how good it is.", key="prec10", delay=.06))
        st.markdown("<div class='disclaimer'>These are estimates from patient wording, not medical advice.</div>", unsafe_allow_html=True)
        if cond == "Unknown" or med == "Unknown":
            st.info("Condition or medication is set to Unknown, which lowers the estimate: unknown entries are usually rare "
                    "medications whose pages get few readers. Choose both for a fair score.")

