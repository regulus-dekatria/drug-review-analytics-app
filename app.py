"""Drug Review Analytics: entry point and navigation."""
import streamlit as st

from core import models_ready, style

st.set_page_config(page_title="Drug Review Analytics", page_icon=":material/medication:", layout="wide")
style()

pages = {
    "Dashboard": [
        st.Page("views/overview.py", title="Overview", icon=":material/dashboard:", default=True),
        st.Page("views/volume.py", title="Volume Analysis", icon=":material/bar_chart:"),
        st.Page("views/ratings.py", title="Average Ratings", icon=":material/star_half:"),
        st.Page("views/dispersion.py", title="Rating Dispersion", icon=":material/swap_vert:"),
        st.Page("views/rankings.py", title="Rankings", icon=":material/leaderboard:"),
        st.Page("views/insights.py", title="Reviews Analysis", icon=":material/insights:"),
        st.Page("views/predictive.py", title="Predictive Insights", icon=":material/online_prediction:"),
    ],
    "Predict": [
        st.Page("views/classify.py", title="Classify a message", icon=":material/chat:"),
        st.Page("views/helpfulness.py", title="Predict helpfulness", icon=":material/thumb_up:"),
    ],
    "Models and data": [
        st.Page("views/performance.py", title="Model performance", icon=":material/monitoring:"),
        st.Page("views/dictionary.py", title="Data dictionary", icon=":material/menu_book:"),
        st.Page("views/about.py", title="About", icon=":material/info:"),
    ],
}
if not models_ready():
    st.error("The model files are missing. Copy the contents of models/run2 from the project Drive into models/run2 in this repository.")
st.navigation(pages).run()
