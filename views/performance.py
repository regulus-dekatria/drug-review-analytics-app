"""Test results and training logs of the predictive models."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import AQUA, BLUE, CYAN, INK, MUTED, NAVY, footer, metrics, training_log

st.title("Model performance")
st.write("Every model learned from reviews posted from 2008 to 2015 and was tested once on 52,524 reviews from 2016 "
         "and 2017 that it never saw. Testing on later years copies real use: trained on the past, applied to new messages.")

m = metrics()
if m is None:
    st.error("models/run2/metrics.json is missing.")
    st.stop()

LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="IBM Plex Sans", color=INK),
              margin=dict(l=10, r=10, t=30, b=10))

o1 = m["objective1"]
st.header("Objective 1 · rating group from text")
served = o1["served"]
s = o1["test"].get(served) or o1["test"].get("DistilBERT", {})
k1, k2, k3, k4 = st.columns(4)
k1.metric("Balanced accuracy", f"{s.get('balanced accuracy', 0) * 100:.1f}%", help="Average hit rate across the three groups.")
k2.metric("Recall on Low", f"{s.get('recall Low', 0) * 100:.1f}%", help="Share of truly Low reviews found.")
k3.metric("Severe errors", f"{s.get('severe error rate', 0) * 100:.1f}%", help="Low called High, or High called Low.")
k4.metric("Low found reading top 20%", f"{o1['capture_rate'].get('20%', 0) * 100:.0f}%", help="Reading in arrival order finds 20%.")
full_only = served not in o1["test"]
st.caption((f"Figures from the full DistilBERT on all 52,524 test reviews; the app serves its compressed copy, checked "
            f"against it on a random sample of test reviews (see the compressed model check below). " if full_only else
            f"Served model: {served}. ") +
           f"Baseline (always High): {o1['test']['Baseline (always High)']['accuracy'] * 100:.1f}% accuracy, 0% recall on Low.")

t1 = pd.DataFrame(o1["test"]).T[["accuracy", "balanced accuracy", "macro F1", "recall Low", "severe error rate"]] * 100
fig = go.Figure()
for col, colour in zip(["balanced accuracy", "recall Low", "severe error rate"], [NAVY, CYAN, AQUA]):
    fig.add_bar(name=col, y=t1.index, x=t1[col], orientation="h", marker_color=colour)
fig.update_layout(barmode="group", height=60 * len(t1) + 80, yaxis=dict(autorange="reversed"),
                  xaxis=dict(title="% of test reviews"), legend=dict(orientation="h", y=1.1), **LAYOUT)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
st.dataframe(t1.round(1), width="stretch")

st.header("Objective 2 · helpful reviews")
o2 = m["objective2"]
s2 = o2["test"][o2["served"]]
c1, c2, c3 = st.columns(3)
c1.metric("ROC AUC", f"{s2['ROC AUC']:.3f}", help="0.5 is chance; 1.0 is perfect ranking.")
c2.metric("Precision in top 10%", f"{s2['precision top 10%'] * 100:.1f}%", help="Share truly helpful among the 10% ranked highest.")
c3.metric("Base rate", f"{o2['base_rate_test'] * 100:.1f}%")
st.caption(f"Served model: {o2['served']}. The text added {o2['text_gain_auc']:+.3f} ROC AUC over rating, length, condition and medication.")
st.dataframe((pd.DataFrame(o2["test"]).T).round(3), width="stretch")

st.header("Training logs")
log = training_log()
if log is None:
    st.info("Copy derived/predictive/training_log_run2.json into data/ to show the training logs.")
else:
    db = log.get("distilbert", {})
    a, b = st.columns(2)
    with a:
        st.subheader("DistilBERT training loss")
        if db.get("stage1_steps"):
            fig = go.Figure()
            s1 = pd.DataFrame(db["stage1_steps"])
            fig.add_scatter(x=s1["step"], y=s1["loss"], name="stage 1 (choose passes)", line=dict(color=BLUE))
            if db.get("stage2_steps"):
                s2_ = pd.DataFrame(db["stage2_steps"])
                fig.add_scatter(x=s2_["step"], y=s2_["loss"], name="stage 2 (final fit)", line=dict(color=NAVY))
            fig.update_layout(height=320, xaxis_title="training step", yaxis_title="loss", legend=dict(orientation="h", y=1.15), **LAYOUT)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            st.caption("The loss falls quickly and then levels off: the model has learned what it can from the data.")
        else:
            st.caption(db.get("status", "DistilBERT was not trained in this run."))
    with b:
        st.subheader("Validation score after each pass")
        if db.get("stage1_passes"):
            p = pd.DataFrame(db["stage1_passes"])
            fig = go.Figure(go.Scatter(x=p["epoch"], y=p["validation_balanced_accuracy"] * 100, mode="lines+markers",
                                       line=dict(color=NAVY, width=3)))
            fig.update_layout(height=320, xaxis=dict(title="pass", dtick=1), yaxis_title="2015 balanced accuracy (%)", **LAYOUT)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            st.caption(f"Passes kept: {db.get('best_passes')}. A rising score means the model is still learning general "
                       f"patterns rather than memorising the training reviews.")
    st.subheader("LightGBM: validation ROC AUC by number of trees")
    fig = go.Figure()
    for (name, g), colour in zip(log.get("lightgbm", {}).items(), [NAVY, BLUE, CYAN]):
        fig.add_scatter(y=g["validation_auc"], name=name, line=dict(color=colour))
        fig.add_scatter(x=[g["best_trees"] - 1], y=[g["validation_auc"][g["best_trees"] - 1]], mode="markers",
                        marker=dict(color=colour, size=10), showlegend=False)
    fig.update_layout(height=320, xaxis_title="trees", yaxis_title="2015 ROC AUC", legend=dict(orientation="h", y=1.15), **LAYOUT)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption("Dots mark where early stopping ended training: adding trees no longer improved the 2015 score.")
    on = log.get("onnx", {})
    if on.get("passed") is not None:
        st.subheader("Compressed model check")
        st.write(f"The served DistilBERT is compressed from {on.get('size_mb_full', 0):.0f} MB to {on.get('size_mb_compressed', 0):.0f} MB. "
                 f"On {on.get('reviews_tested', 0):,} test reviews it gives the same group as the full model "
                 f"{on.get('agreement_with_full', 0) * 100:.2f}% of the time, with balanced accuracy "
                 f"{on.get('balanced_accuracy_compressed', 0) * 100:.1f}% against {on.get('balanced_accuracy_full', 0) * 100:.1f}%. "
                 f"One message takes about {on.get('median_ms_per_message', 0):.0f} ms on a plain processor.")

footer()
