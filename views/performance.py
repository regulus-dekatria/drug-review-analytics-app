"""Test results and training logs of the predictive models, and the checks on the review text analysis."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import AQUA, BLUE, CYAN, NAVY, metrics, plot_layout, reviews_analysis, training_log
from dash import bars, box, card, hero, kpis, legend, note, row, title_case

hero("Model Performance")
m = metrics()
if m is None:
    st.error("models/run2/metrics.json is missing.")
    st.stop()


def section(title):
    st.markdown(f"<div class='sec-h'>{title}</div>", unsafe_allow_html=True)


o1 = m["objective1"]
served = o1["served"]
s = o1["test"].get(served) or o1["test"].get("DistilBERT", {})
section("Rating Group Model")
st.markdown(kpis([
    ("Balanced Accuracy", f"{s.get('balanced accuracy', 0) * 100:.1f}%", "average hit rate across Low, Middle and High", "balacc", "target"),
    ("Recall on Low", f"{s.get('recall Low', 0) * 100:.1f}%", "truly Low reviews found", "recall_low", "sentiment_dissatisfied"),
    ("Severe Errors", f"{s.get('severe error rate', 0) * 100:.1f}%", "Low called High, or High called Low", "severe", "error"),
    ("Low Found in the Top 20%", f"{o1['capture_rate'].get('20%', 0) * 100:.1f}%", "reading in arrival order finds 20%", "capture", "manage_search")]),
    unsafe_allow_html=True)

t1 = pd.DataFrame(o1["test"]).T[["accuracy", "balanced accuracy", "macro F1", "recall Low", "severe error rate"]]
order = t1.sort_values("balanced accuracy", ascending=False).index
lead = order[0]
base = o1["test"]["Baseline (always High)"]["accuracy"]
row(card("Balanced Accuracy by Model", bars(t1.loc[order, "balanced accuracy"], lambda v: f"{v * 100:.1f}%", lead=lead, label_w=230, scale=1),
         f"{lead} is the strongest model. The app serves its compressed copy (checked below). A model that always answers High "
         f"scores {base * 100:.1f}% plain accuracy but finds no Low reviews at all.", key="balacc", delay=.04,
         lead="Tested once on 52,524 reviews from 2016 and 2017 that no model saw in training."),
    card("Severe Errors by Model", bars(t1.loc[order, "severe error rate"], lambda v: f"{v * 100:.1f}%", lead=lead, label_w=230, scale=t1["severe error rate"].max() or 1),
         "Fewer severe errors means fewer complaints filed with the praise. Lower is better.", key="severe", delay=.08,
         lead="Share of reviews put at the opposite end of the scale."))
with box("Rating Group Results", "perf-o1", key="balacc"):
    pc = lambda label: st.column_config.NumberColumn(label, format="%.1f%%")
    st.dataframe(t1.loc[order] * 100, width="stretch", column_config={
        "_index": st.column_config.TextColumn("Model"), "accuracy": pc("Accuracy"), "balanced accuracy": pc("Balanced Accuracy"),
        "macro F1": pc("Macro F1"), "recall Low": pc("Recall on Low"), "severe error rate": pc("Severe Errors")})

o2 = m["objective2"]
s2 = o2["test"][o2["served"]]
section("Helpfulness Model")
st.markdown(kpis([
    ("ROC AUC", f"{s2['ROC AUC']:.3f}", "0.5 is chance, 1.0 is perfect", "auc", "show_chart"),
    ("Precision in the Top 10%", f"{s2['precision top 10%'] * 100:.1f}%", "truly helpful among the highest ranked", "prec10", "workspace_premium"),
    ("Base Rate", f"{o2['base_rate_test'] * 100:.1f}%", "reviews that are truly helpful", None, "percent")], n=3), unsafe_allow_html=True)
with box("Helpfulness Results", "perf-o2", key="auc"):
    t2 = pd.DataFrame(o2["test"]).T
    t2 = t2.sort_values("ROC AUC", ascending=False) if "ROC AUC" in t2 else t2
    st.dataframe(t2, width="stretch", column_config={"_index": st.column_config.TextColumn("Model"),
                 **{c: st.column_config.NumberColumn(title_case(c.replace("roc auc", "ROC AUC")), format="%.3f") for c in t2.columns}})
    note(f"Served model: {o2['served']}. Adding the review text changed ROC AUC by {o2['text_gain_auc']:+.3f}, so the app uses the "
         f"rating, length, condition and medication only.")

section("Training Logs")
log = training_log()
if log is None:
    st.info("Copy training_log_run2.json into data/ to show the training logs.")
else:
    db = log.get("distilbert", {})
    a, b = st.columns(2)
    with a:
        with box("DistilBERT Training Loss", "perf-loss"):
            if db.get("stage1_steps"):
                fig = go.Figure()
                s1 = pd.DataFrame(db["stage1_steps"])
                fig.add_scatter(x=s1["step"], y=s1["loss"], name="stage 1 (choose passes)", line=dict(color=CYAN, width=2))
                if db.get("stage2_steps"):
                    s2_ = pd.DataFrame(db["stage2_steps"])
                    fig.add_scatter(x=s2_["step"], y=s2_["loss"], name="stage 2 (final fit)", line=dict(color=NAVY, width=2))
                fig.update_layout(**plot_layout(300), xaxis_title="training step", yaxis_title="loss")
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
                note("The loss falls quickly, then levels off: the model has learned what it can from the data.")
            else:
                note(db.get("status", "DistilBERT was not trained in this run."))
    with b:
        with box("Validation Score After Each Pass", "perf-passes"):
            if db.get("stage1_passes"):
                p = pd.DataFrame(db["stage1_passes"])
                fig = go.Figure(go.Scatter(x=p["epoch"], y=p["validation_balanced_accuracy"] * 100, mode="lines+markers",
                                           line=dict(color=NAVY, width=3), marker=dict(size=9, color=NAVY)))
                fig.update_layout(**plot_layout(300), xaxis=dict(title="pass", dtick=1), yaxis_title="2015 balanced accuracy (%)")
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
                note(f"Passes kept: {db.get('best_passes')}. A rising score means the model is still learning general patterns, "
                     f"not memorising the training reviews.")
    with box("LightGBM: Validation ROC AUC by Number of Trees", "perf-trees"):
        fig = go.Figure()
        for (name, g), colour in zip(log.get("lightgbm", {}).items(), [NAVY, BLUE, CYAN]):
            fig.add_scatter(y=g["validation_auc"], name=name, line=dict(color=colour, width=2))
            fig.add_scatter(x=[g["best_trees"] - 1], y=[g["validation_auc"][g["best_trees"] - 1]], mode="markers",
                            marker=dict(color=colour, size=10), showlegend=False)
        fig.update_layout(**plot_layout(300), xaxis_title="trees", yaxis_title="2015 ROC AUC")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        note("Dots mark where early stopping ended training: more trees no longer improved the 2015 score.")
    on = log.get("onnx", {})
    if on.get("passed") is not None:
        st.markdown(card("Compressed Model Check",
                         f"<div class='lead-in'>The served DistilBERT is compressed from {on.get('size_mb_full', 0):.0f} MB to "
                         f"{on.get('size_mb_compressed', 0):.0f} MB so it runs on a plain processor.</div>",
                         f"On {on.get('reviews_tested', 0):,} test reviews it gives the same group as the full model "
                         f"{on.get('agreement_with_full', 0) * 100:.2f}% of the time, with balanced accuracy "
                         f"{on.get('balanced_accuracy_compressed', 0) * 100:.1f}% against {on.get('balanced_accuracy_full', 0) * 100:.1f}%. "
                         f"One message takes about {on.get('median_ms_per_message', 0):.0f} ms.", delay=.04), unsafe_allow_html=True)

ra = reviews_analysis()
val = (ra or {}).get("validation") or {}
if val:
    section("Review Text Analysis Checks")
    st.markdown(kpis([
        ("VADER Agreement", f"{val.get('vader_accuracy', 0):.1f}%", f"with the rating group; Cohen's kappa {val.get('vader_kappa', 0):.3f}", "vader_agree", "rule"),
        ("Theme Coherence", f"{val.get('theme_coherence', 0):.3f}", "NPMI of each theme's top words", None, "hub"),
        ("Theme Stability", f"{val.get('theme_stability', 0):.3f}", "ARI across random seeds", None, "lock"),
        ("Negated Symptom Mentions", f"{val.get('symptom_mentions_negated', 0):.1f}%", "follow a word like \"no\"", None, "block")]),
        unsafe_allow_html=True)
