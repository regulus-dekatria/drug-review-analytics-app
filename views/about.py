"""What the app is for, how it was built, and its limits."""
import streamlit as st

from core import footer, manifest

st.title("About")
st.markdown("""
**Drug Review Analytics** helps pharmacy managers and drug safety teams read patient feedback at scale. It was built
for the Analytics Techniques and Tools course at Jose Rizal University, on the UCI Drug Review dataset
(Drugs.com reviews posted from 2008 to 2017).

#### What it does

| Page | Use |
|---|---|
| Classify a message | Estimate the rating group of an unrated message and list the topics it raises, so poor experiences are read first |
| Predict helpfulness | Estimate whether a new review will rank among the most helpful of its month |
| Review insights | Sentiment, watchlist topics, themes and words across all reviews or one condition |
| Model performance | Test results, the comparison with a no-skill baseline, and the training logs |

#### How the models were built

- **Rating group:** DistilBERT, a transformer encoder, fine-tuned on reviews from 2008 to 2015, then compressed to
  8-bit ONNX so it runs on a plain processor. A TF-IDF logistic regression is kept as the fallback.
- **Helpfulness:** LightGBM on the star rating, review length, condition and medication. Helpful means the top 25%
  of helpful votes among reviews posted in the same month.
- **Watchlist:** the same terms and rules as the NLP notebook. Dose amounts are found with a simpler pattern than
  the one used in data cleaning.

#### Limits

- English only. Messages in other languages, or mixed languages such as Taglish, are less reliable.
- The rating group estimates the star rating a patient would give. It is not a clinical judgement and not medical advice.
- The models learned from Drugs.com reviews; messages from other channels may be written differently.
- Helpfulness partly reflects how many readers a medication's page gets, not only the quality of the review.
- Nothing you type is stored. The test log on the Classify page stays in your browser session until you download it.
""")
m = manifest()
if m:
    with st.expander("Model versions"):
        st.json({"run": m.get("run"), "created": m.get("created"), "served": {"rating group": m.get("objective1_served"),
                 "helpfulness": m.get("objective2_served")}, "libraries": m.get("versions")})
footer()
