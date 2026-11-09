"""Classify a patient message into a rating group, with watchlist topics."""
from datetime import datetime

import pandas as pd
import streamlit as st

import watchlist
from core import (DATA_DIR, GROUPS, categories, models_ready, prob_bars, served_name, served_probs,
                  tfidf_probs, word_pushes, preprocessing)
from dash import box, card, esc, kpis, row

from dash import hero
hero("Classify a Message")

if not models_ready():
    st.stop()

if "soft_log" not in st.session_state:
    st.session_state.soft_log = []
keep = watchlist.kept_terms(DATA_DIR / "watchlist_term_frequency.csv")

single, batch = st.tabs(["One Message", "Many Messages (CSV)"])

with single:
    with st.form("classify"):
        text = st.text_area("Patient message", height=140, max_chars=3000,
                            help="Paste a message without a star rating. The model estimates whether the patient would rate "
                                 "the experience Low (1 to 3), Middle (4 to 7) or High (8 to 10), and lists the topics it raises.",
                            placeholder="e.g. Made me so dizzy I could not drive. Stopped after a week.")
        condition = st.selectbox("Condition (optional, improves the side-effect list)", ["Unknown"] +
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
            hits = watchlist.scan(text, condition, keep)
            action = {"Low": "Read and respond first. This message most likely describes a poor experience.",
                      "Middle": "A mixed experience. Check the topics on the right for what went wrong.",
                      "High": "Most likely a positive experience. No follow-up needed unless a topic stands out."}[group]
            topics = ""
            for cat in watchlist.CATEGORY_ORDER:
                terms = [h for h in hits if h["category"] == cat]
                if terms:
                    tags = "".join(f"<span class='tag {'plain absent' if h['negated'] and cat == watchlist.SE else 'plain'}'>{esc(h['term'])}</span>"
                                   for h in terms)
                    topics += f"<div class='sublabel'>{esc(cat)}</div><div class='tags'>{tags}</div>"
            negated = any(h["negated"] and h["category"] == watchlist.SE for h in hits)
            row(card("Predicted Rating Group", prob_bars(p, "Most likely group") + f"<div class='action'><b>Suggested action:</b> {action}</div>",
                     key="groups", delay=.02),
                card("Topics Raised", topics or "<div class='lead-in'>No watchlist topics found in this message.</div>",
                     "Struck-through terms follow a word like \"no\" (\"no nausea\"), so the symptom may be absent." if negated else "",
                     key="watchlist", delay=.06))
            st.markdown("<div class='disclaimer'>These are estimates from patient wording, not medical advice.</div>", unsafe_allow_html=True)
            with st.expander("Compare with the Word-Based Model"):
                pt = tfidf_probs([text])[0]
                st.markdown(f"<div class='card'>{prob_bars(pt, 'Word-based model')}</div>", unsafe_allow_html=True)
                low, high = word_pushes(text)
                st.write(f"Words pushing toward Low: **{', '.join(low) or '-'}**")
                st.write(f"Words pushing toward High: **{', '.join(high) or '-'}**")
                st.caption("The main model reads whole sentences; this one counts words. When they disagree, the message "
                           "is usually mixed or depends on context.")
            st.session_state.last = {"time": datetime.now().isoformat(timespec="seconds"), "message": text,
                                     "condition": condition, "model": served_name(), "predicted": group,
                                     **{f"p_{g.lower()}": round(float(v), 3) for g, v in zip(GROUPS, p)},
                                     "topics": "; ".join(sorted({h["category"] for h in hits}))}

    if st.session_state.get("last"):
        st.markdown("<div class='qt'>Test Log</div>", unsafe_allow_html=True)
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
        st.markdown(kpis([("Messages Recorded", f"{len(df)}", "this session", None, "list_alt"),
                          ("You Agree With the Model", f"{df['agree'].mean() * 100:.1f}%", "of recorded messages", None, "handshake")], n=2),
                    unsafe_allow_html=True)
        st.dataframe(df[["message", "predicted", "your_call", "agree", "topics"]], hide_index=True, width="stretch")
        st.download_button("Download test log (CSV)", df.to_csv(index=False).encode(), "soft_test_log_app.csv", "text/csv")
        st.caption("The log lives only in this browser session; download it before closing the page.")

with batch:
    up = st.file_uploader("CSV file with a column named message (up to 500 rows)", type="csv",
                          help="Results are sorted with the most likely poor experiences first, so the team can read from the top.")
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
            icons = {"Low": "sentiment_dissatisfied", "Middle": "sentiment_neutral", "High": "sentiment_satisfied"}
            st.markdown(kpis([(g, f"{counts[g]:,}", f"{counts[g] / len(df) * 100:.1f}% of messages", "groups", icons[g]) for g in GROUPS], n=3),
                        unsafe_allow_html=True)
            st.dataframe(df, hide_index=True, width="stretch")
            st.download_button("Download results (CSV)", df.to_csv(index=False).encode(), "classified_messages.csv", "text/csv")

