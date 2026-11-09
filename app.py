"""Drug Review Analytics: entry point and navigation."""
import streamlit as st

from core import models_ready, style

st.set_page_config(page_title="Drug Review Analytics", page_icon=":material/medication:", layout="wide")
style()

# Keep the shared filters when moving to a page that does not draw them (Streamlit drops a widget's value otherwise).
for _k in ("f_cond", "f_med", "f_ratings", "f_years", "f_preset"):
    if _k in st.session_state:
        st.session_state[_k] = st.session_state[_k]

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
        st.Page("views/classify.py", title="Classify a Message", icon=":material/chat:"),
        st.Page("views/helpfulness.py", title="Predict Helpfulness", icon=":material/thumb_up:"),
    ],
    "Models and Data": [
        st.Page("views/performance.py", title="Model Performance", icon=":material/monitoring:"),
        st.Page("views/records.py", title="Records", icon=":material/table_rows:"),
        st.Page("views/dictionary.py", title="Data Dictionary", icon=":material/menu_book:"),
    ],
}
if not models_ready():
    st.error("The model files are missing. Copy the contents of models/run2 from the project Drive into models/run2 in this repository.")
st.navigation(pages, expanded=True).run()
