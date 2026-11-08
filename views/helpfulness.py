"""Predict whether a new review will be among the most helpful of its month."""
import streamlit as st

from core import categories, footer, helpfulness, models_ready, preprocessing

st.title("Predict helpfulness")
st.write("Enter a new review and its details. The model estimates the chance that readers will rank it in the top "
         "25% of helpful votes among reviews posted in the same month.")

if not models_ready():
    st.stop()

cats = categories()
with st.form("help"):
    text = st.text_area("Review", height=140, max_chars=3000)
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
            band = "among the top 10% of 2016-2017 reviews by score"
        elif q and score >= q.get(0.75, 1):
            band = "in the top 25% of 2016-2017 reviews by score"
        elif q and score >= q.get(0.5, 1):
            band = "above the median of 2016-2017 reviews"
        else:
            band = "below the median of 2016-2017 reviews"
        verdict = "Likely helpful" if q and score >= q.get(0.75, 1) else "Not likely in the top 25%"
        st.markdown(f"<div class='card'><div class='label'>{preprocessing().get('objective2_served', '')} model</div>"
                    f"<div class='big'>{verdict}</div>"
                    f"<div><span class='num'>{score * 100:.0f}%</span> chance · scores {band}</div>"
                    f"<div class='label'>{len(text.split())} words · rating {rating} · {cond} · {med}</div></div>",
                    unsafe_allow_html=True)
        if cond == "Unknown" or med == "Unknown":
            st.info("Condition or medication is set to Unknown. In the training data, Unknown mostly means rare or "
                    "unrecognised entries whose pages get few readers, so leaving them unset lowers the estimate. "
                    "Choose both for a fair score.")
        st.caption("The base rate is about 25%: one review in four reaches the top quarter of its month. Condition and "
                   "medication weigh heavily because popular medications' pages get more readers, so part of the score "
                   "reflects how many people will see the review, not only how good it is.")

footer()
