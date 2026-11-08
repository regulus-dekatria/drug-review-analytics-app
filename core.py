"""Model loading, scoring and shared styling for the Drug Review Analytics app."""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
MODEL_DIR = ROOT / "models" / "run2"
DATA_DIR = ROOT / "data"
GROUPS = ["Low", "Middle", "High"]

NAVY, BLUE, CYAN, AQUA, ICE, CARD = "#0D47A1", "#1976D2", "#00ACC1", "#4DD0E1", "#E0F7FA", "#CCF1F6"
INK, MUTED = "#0B2545", "#34506A"
GROUP_COLOURS = {"Low": NAVY, "Middle": BLUE, "High": CYAN}


# ------------------------------------------------------------------ styling
def style():
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&family=Plus+Jakarta+Sans:wght@600&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@500&display=swap');
html, body, .stMarkdown, p, li, label, input, textarea, button {{ font-family: 'IBM Plex Sans', sans-serif; }}
[data-testid="stIconMaterial"], .material-symbols-rounded {{ font-family: 'Material Symbols Rounded' !important; }}
h1 {{ font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; color: {INK}; letter-spacing: -0.01em; }}
h2, h3, h4 {{ font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 600 !important; color: {INK}; }}
[data-testid="stMetricValue"], .num {{ font-family: 'IBM Plex Mono', monospace !important; }}
.card {{ background: {CARD}; border-radius: 14px; padding: 16px 20px; margin: 8px 0 14px;
        box-shadow: 0 1px 2px rgba(13,71,161,.08), 0 6px 18px rgba(13,71,161,.06); }}
.card .label {{ color: {MUTED}; font-size: 0.82rem; }}
.card .big {{ font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 700; color: {INK}; line-height: 1.2; }}
.bar {{ display:flex; align-items:center; gap:10px; margin:4px 0; }}
.bar .name {{ width:64px; color:{INK}; }}
.bar .track {{ flex:1; background:{ICE}; border-radius:7px; height:14px; overflow:hidden; }}
.bar .fill {{ height:14px; border-radius:7px; }}
.bar .pct {{ width:48px; text-align:right; font-family:'IBM Plex Mono', monospace; color:{INK}; }}
.chip {{ display:inline-block; background:{ICE}; color:{INK}; border-radius:999px; padding:2px 10px; margin:2px 4px 2px 0; font-size:0.85rem; }}
.chip.absent {{ text-decoration: line-through; color:{MUTED}; }}
@media (prefers-reduced-motion: no-preference) {{ .bar .fill {{ transition: width .6s ease; }} }}
</style>""", unsafe_allow_html=True)


def footer():
    m = manifest()
    served = (f"Rating groups: {m.get('objective1_served', 'n/a')} · Helpfulness: {m.get('objective2_served', 'n/a')}"
              if m else "Models not found")
    st.markdown("---")
    st.caption(f"Model run {m.get('run', '?') if m else '?'} · {served} · Trained on reviews from 2008-2015 and "
               f"tested on 2016-2017. Not medical advice.")


def prob_bars(p, title):
    rows = "".join(f"<div class='bar'><span class='name'>{g}</span><div class='track'>"
                   f"<div class='fill' style='width:{v * 100:.1f}%;background:{GROUP_COLOURS[g]}'></div></div>"
                   f"<span class='pct'>{v * 100:.0f}%</span></div>" for g, v in zip(GROUPS, p))
    return (f"<div class='card'><div class='label'>{title}</div>"
            f"<div class='big'>{GROUPS[int(np.argmax(p))]}</div>{rows}</div>")


# ------------------------------------------------------------------ loading
def _json(path):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else None


@st.cache_resource
def manifest():
    return _json(MODEL_DIR / "manifest.json")


@st.cache_resource
def preprocessing():
    return _json(MODEL_DIR / "preprocessing.json")


@st.cache_resource
def metrics():
    return _json(MODEL_DIR / "metrics.json")


@st.cache_resource
def categories():
    return _json(MODEL_DIR / "categories.json") or {"conditions": ["Unknown"], "medications": ["Unknown"]}


@st.cache_resource
def reviews_analysis():
    return _json(DATA_DIR / "reviews_analysis.json")


@st.cache_resource
def training_log():
    logs = sorted(DATA_DIR.glob("training_log_run*.json"))
    return _json(logs[-1]) if logs else None


@st.cache_resource
def tfidf_parts():
    import joblib
    vec = joblib.load(MODEL_DIR / "tfidf_vectoriser.joblib")
    model = joblib.load(MODEL_DIR / "objective1_fallback_model.joblib")
    return vec, model


@st.cache_resource
def bert_parts():
    # The compressed DistilBERT and its tokenizer; None when the run did not ship one.
    d = MODEL_DIR / "distilbert_onnx"
    if not (d / "model_int8.onnx").exists():
        return None
    import onnxruntime as ort
    from tokenizers import Tokenizer
    cfg = (preprocessing() or {}).get("objective1_onnx") or {}
    tok = Tokenizer.from_file(str(d / "tokenizer.json"))
    tok.enable_truncation(max_length=int(cfg.get("max_length", 256)))
    pad_id = tok.token_to_id("[PAD]")
    tok.enable_padding(pad_id=0 if pad_id is None else pad_id, pad_token="[PAD]")
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    sess = ort.InferenceSession(str(d / "model_int8.onnx"), opts, providers=["CPUExecutionProvider"])
    return tok, sess


@st.cache_resource
def helpfulness_parts():
    import lightgbm as lgb
    booster = lgb.Booster(model_file=str(MODEL_DIR / "objective2_lightgbm.txt"))
    svd = None
    if (MODEL_DIR / "objective2_svd.joblib").exists() and (preprocessing() or {}).get("objective2_served") == "Structured + text":
        import joblib
        svd = joblib.load(MODEL_DIR / "objective2_svd.joblib")
    return booster, svd


def models_ready():
    return (MODEL_DIR / "manifest.json").exists()


# ------------------------------------------------------------------ scoring
def to_tokens(raw):
    # Rebuilds the NLP notebook's word list from the exported rules.
    cfg = preprocessing()
    t = str(raw).lower()
    for a, b in cfg["apostrophes"].items():
        t = t.replace(a, b)
    for pattern, repl in cfg["contractions"]:
        t = re.sub(pattern, repl, t)
    t = t.replace("'", "")
    stop = _stopwords()
    return " ".join(w for w in re.findall(cfg["word_pattern"], t) if w not in stop)


@st.cache_resource
def _stopwords():
    return frozenset(preprocessing()["stopwords"])


def tfidf_probs(texts):
    vec, model = tfidf_parts()
    X = vec.transform([to_tokens(t) for t in texts])
    if isinstance(model, dict):                      # ordinal fallback saved as its parts
        a = model["above_low"].predict_proba(X)[:, 1]
        b = np.minimum(model["above_middle"].predict_proba(X)[:, 1], a)
        p = np.column_stack([1 - a, a - b, b])
        return p / p.sum(1, keepdims=True)
    return model.predict_proba(X)


def bert_probs(texts, batch=32):
    tok, sess = bert_parts()
    texts = list(texts)
    order = np.argsort([len(t) for t in texts])
    out = np.zeros((len(texts), 3), dtype=np.float32)
    for i in range(0, len(texts), batch):
        idx = order[i:i + batch]
        enc = tok.encode_batch([texts[j] for j in idx])
        ids = np.array([e.ids for e in enc], dtype=np.int64)
        mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
        logits = sess.run(None, {"input_ids": ids, "attention_mask": mask})[0]
        e = np.exp(logits - logits.max(1, keepdims=True))
        out[idx] = e / e.sum(1, keepdims=True)
    return out


def served_name():
    cfg = preprocessing() or {}
    if bert_parts() is not None and str(cfg.get("objective1_served", "")).startswith("DistilBERT"):
        return cfg["objective1_served"]
    return cfg.get("objective1_fallback", "TF-IDF + LR")


def served_probs(texts):
    return bert_probs(texts) if served_name().startswith("DistilBERT") else tfidf_probs(texts)


def word_pushes(text, k=6):
    # Words that pushed the TF-IDF model toward Low or toward High (only for a plain logistic regression fallback).
    vec, model = tfidf_parts()
    if isinstance(model, dict):
        coef_low, coef_high = -model["above_low"].coef_[0], model["above_middle"].coef_[0]
    else:
        coef_low, coef_high = model.coef_[0], model.coef_[2]
    x = vec.transform([to_tokens(text)])
    if x.nnz == 0:
        return [], []
    vocab = vec.get_feature_names_out()
    low = [vocab[i] for i, c in sorted(zip(x.indices, coef_low[x.indices] * x.data), key=lambda z: -z[1])[:k] if c > 0]
    high = [vocab[i] for i, c in sorted(zip(x.indices, coef_high[x.indices] * x.data), key=lambda z: -z[1])[:k] if c > 0]
    return low, high


def helpfulness(text, rating, condition, medication):
    booster, svd = helpfulness_parts()
    cats = categories()
    cond = condition if condition in cats["conditions"] else "Unknown"
    med = medication if medication in cats["medications"] else "Unknown"
    f = pd.DataFrame({"rating": [float(rating)], "review_words": [float(len(str(text).split()))],
                      "condition": pd.Categorical([cond], categories=cats["conditions"]),
                      "medication": pd.Categorical([med], categories=cats["medications"])})
    if svd is not None:
        vec, _ = tfidf_parts()
        S = svd.transform(vec.transform([to_tokens(text)]))
        f = pd.concat([f, pd.DataFrame(S, columns=[f"text_{i}" for i in range(S.shape[1])])], axis=1)
    return float(booster.predict(f)[0]), cond, med
