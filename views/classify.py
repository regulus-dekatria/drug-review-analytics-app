"""Classify a patient message into a rating group, with watchlist topics."""
from datetime import datetime

import pandas as pd
import streamlit as st

import watchlist
from core import (DATA_DIR, GROUPS, categories, footer, models_ready, prob_bars, served_name, served_probs,
                  tfidf_probs, word_pushes, preprocessing)

st.title("Classify a message")
st.write("Paste an unrated patient message. The model estimates which rating group the patient would most likely "
         "give (Low 1-3, Middle 4-7, High 8-10) and lists the watchlist topics the message mentions.")

if not models_ready():
    st.stop()

if "soft_log" not in st.session_state:
    st.session_state.soft_log = []
keep = watchlist.kept_terms(DATA_DIR / "watchlist_term_frequency.csv")

single, batch = st.tabs(["One message", "Many messages (CSV)"])

with single:
    with st.form("classify"):
        text = st.text_area("Patient message", height=140, max_chars=3000,
                            placeholder="e.g. Made me so dizzy I could not drive. Stopped after a week.")
        condition = st.selectbox("Condition (optional, sharpens the side-effect list)", ["Unknown"] +
                                 [c for c in categories()["conditions"] if c != "Unknown"], index=0)
        submitted = st.form_submit_button("Classify", type="primary")

    if submitted:
        words = len(text.split())
        if words == 0:
            st.warning("Type or paste a message first.")
        else:
            if words < 4:
                st.info("Very short messages give the model little to read, so treat this result with caution.")
            p = served_probs([text])[0]
            group = GROUPS[int(p.argmax())]
            left, right = st.columns([1.1, 1])
            with left:
                st.markdown(prob_bars(p, f"Predicted rating group · {served_name()}"), unsafe_allow_html=True)
                if group == "Low":
                    st.markdown("**Suggested action:** read and respond first; this message likely describes a poor experience.")
                elif group == "Middle":
                    st.markdown("**Suggested action:** mixed experience; check the watchlist topics for what went wrong.")
                else:
                    st.markdown("**Suggested action:** likely a positive experience; no follow-up needed unless a topic below stands out.")
            with right:
                hits = watchlist.scan(text, condition, keep)
                st.markdown("**Watchlist topics**")
                if not hits:
                    st.caption("No watchlist terms found.")
                for cat in watchlist.CATEGORY_ORDER:
                    terms = [h for h in hits if h["category"] == cat]
                    if terms:
                        chips = "".join(f"<span class='chip{' absent' if h['negated'] and cat == watchlist.SE else ''}'>{h['term']}</span>"
                                        for h in terms)
                        st.markdown(f"{cat}<br>{chips}", unsafe_allow_html=True)
                if any(h["negated"] and h["category"] == watchlist.SE for h in hits):
                    st.caption("Struck-through terms follow a negation (\"no nausea\"), so they may describe an absent symptom.")
            with st.expander("Compare with the word-based model"):
                pt = tfidf_probs([text])[0]
                st.markdown(prob_bars(pt, f"Word-based model · {preprocessing().get('objective1_fallback', 'TF-IDF')}"), unsafe_allow_html=True)
                low, high = word_pushes(text)
                st.write(f"Words pushing toward Low: **{', '.join(low) or '-'}**")
                st.write(f"Words pushing toward High: **{', '.join(high) or '-'}**")
                st.caption("The served model reads whole sentences; the word-based model counts words. Where they disagree, "
                           "the message is usually mixed or depends on context.")
            st.session_state.last = {"time": datetime.now().isoformat(timespec="seconds"), "message": text,
                                     "condition": condition, "model": served_name(), "predicted": group,
                                     **{f"p_{g.lower()}": round(float(v), 3) for g, v in zip(GROUPS, p)},
                                     "topics": "; ".join(sorted({h["category"] for h in hits}))}

    if st.session_state.get("last"):
        st.markdown("#### Test log")
        c1, c2 = st.columns([2, 1])
        call = c1.radio("Which group would you give this message?", GROUPS, horizontal=True, index=None, key=f"call_{len(st.session_state.soft_log)}")
        if c2.button("Record", disabled=call is None):
            row = {**st.session_state.last, "your_call": call, "agree": call == st.session_state.last["predicted"]}
            st.session_state.soft_log.append(row)
            st.session_state.last = None
            st.rerun()
    log = st.session_state.soft_log
    if log:
        df = pd.DataFrame(log)
        st.caption(f"{len(df)} recorded this session · you agree with the model on {df['agree'].mean() * 100:.0f}%")
        st.dataframe(df[["message", "predicted", "your_call", "agree", "topics"]], hide_index=True, width="stretch")
        st.download_button("Download test log (CSV)", df.to_csv(index=False).encode(), "soft_test_log_app.csv", "text/csv")
        st.caption("The log lives only in this browser session; download it before closing the page.")

with batch:
    st.write("Upload a CSV with a column named **message** (up to 500 rows). Messages are sorted with the most likely "
             "poor experiences first, so a team can read from the top.")
    up = st.file_uploader("CSV file", type="csv")
    if up is not None:
        try:
            df = pd.read_csv(up)
        except Exception as e:
            st.error(f"Could not read the file: {e}")
            st.stop()
        if "message" not in df.columns:
            st.error("The file needs a column named 'message'.")
        else:
            df = df.dropna(subset=["message"]).head(500).copy()
            with st.spinner(f"Classifying {len(df)} messages..."):
                p = served_probs(df["message"].astype(str).tolist())
            df["predicted"] = [GROUPS[i] for i in p.argmax(1)]
            for i, g in enumerate(GROUPS):
                df[f"p_{g.lower()}"] = p[:, i].round(3)
            df["topics"] = ["; ".join(sorted({h["category"] for h in watchlist.scan(m, "Unknown", keep)})) for m in df["message"].astype(str)]
            df = df.sort_values("p_low", ascending=False)
            counts = df["predicted"].value_counts().reindex(GROUPS, fill_value=0)
            m1, m2, m3 = st.columns(3)
            for col, g in zip((m1, m2, m3), GROUPS):
                col.metric(g, f"{counts[g]:,}", f"{counts[g] / len(df) * 100:.0f}% of messages", delta_color="off")
            st.dataframe(df, hide_index=True, width="stretch")
            st.download_button("Download results (CSV)", df.to_csv(index=False).encode(), "classified_messages.csv", "text/csv")

footer()
