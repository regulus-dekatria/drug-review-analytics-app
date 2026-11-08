"""Drug Review Analytics: entry point and navigation."""
import streamlit as st

from core import models_ready, style

st.set_page_config(page_title="Drug Review Analytics", page_icon=":material/medication:", layout="wide")
style()

pages = {
    "Predict": [
        st.Page("views/classify.py", title="Classify a message", icon=":material/chat:", default=True),
        st.Page("views/helpfulness.py", title="Predict helpfulness", icon=":material/thumb_up:"),
    ],
    "Explore": [
        st.Page("views/insights.py", title="Review insights", icon=":material/insights:"),
        st.Page("views/performance.py", title="Model performance", icon=":material/monitoring:"),
        st.Page("views/about.py", title="About", icon=":material/info:"),
    ],
}
if not models_ready():
    st.error("The model files are missing. Copy the contents of models/run2 from the project Drive into models/run2 in this repository.")
st.navigation(pages).run()
