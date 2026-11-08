"""Keyword watchlist: the same terms and rules as Section 4 of the NLP notebook (Run 2), for single messages."""
import re
from pathlib import Path

import pandas as pd

SE = "Side Effects and Symptoms"
WORKED, NOT_WORKED = "Effectiveness: worked", "Effectiveness: did not work"
WATCHLIST = {
    SE: [
        "weight gain", "gained weight", "nausea", "nauseous", "vomiting", "headache", "headaches", "migraine",
        "dizziness", "dizzy", "drowsy", "drowsiness", "fatigue", "tired", "sleepy", "insomnia", "can't sleep",
        "mood swings", "irritability", "anxiety", "depression", "acne", "hair loss", "rash", "itching",
        "dry mouth", "sweating", "constipation", "diarrhea", "bloating", "cramps", "cramping", "spotting",
        "bleeding", "low libido", "sex drive", "palpitations", "tremors", "blurred vision"],
    "Switching Medications": [
        "switched to", "switched from", "changed to", "moved to", "came off", "stopped taking", "went back to",
        "compared to"],
    "Cost": [
        "expensive", "cost", "price", "afford", "affordable", "out of pocket", "insurance", "covered",
        "coverage", "copay", "prior authorization", "coupon", "discount card", "generic"],
    WORKED: [
        "works great", "really works", "worked wonders", "life saver", "helped", "relief", "effective"],
    NOT_WORKED: [
        "didn't work", "doesn't work", "stopped working", "not working", "no effect", "no difference",
        "useless", "waste of money"],
    "Dosage": [
        "increased my dose", "upped the dose", "upped my dose", "lowered my dose", "decreased my dose",
        "half a pill", "once a day", "twice a day"],
}
# Symptom terms that describe the review's own condition or a closely related one, by condition.
RELATED = {
    "depression": {"depression", "anxiety", "mood swings", "irritability"},
    "major depressive disorder": {"depression", "anxiety", "mood swings"},
    "anxiety": {"anxiety", "depression"},
    "anxiety and stress": {"anxiety", "depression"},
    "generalized anxiety disorder": {"anxiety", "depression"},
    "panic disorder": {"anxiety", "depression"},
    "bipolar disorder": {"depression", "anxiety", "mood swings", "irritability"},
    "insomnia": {"insomnia", "can't sleep", "tired", "sleepy", "drowsy", "drowsiness", "fatigue"},
    "vaginal yeast infection": {"itching"},
    "acne": {"acne"},
    "migraine": {"migraine", "headache", "headaches"},
    "migraine prevention": {"migraine", "headache", "headaches"},
    "headache": {"headache", "headaches", "migraine"},
    "irritable bowel syndrome": {"constipation", "diarrhea", "bloating", "cramps", "cramping"},
    "constipation": {"constipation", "bloating"},
    "diarrhea": {"diarrhea"},
    "nausea/vomiting": {"nausea", "nauseous", "vomiting"},
    "abnormal uterine bleeding": {"bleeding", "spotting", "cramps", "cramping"},
    "fibromyalgia": {"fatigue", "tired"},
}
MIN_TERM_REVIEWS = 20
CATEGORY_ORDER = [SE, "Switching Medications", "Cost", WORKED, NOT_WORKED, "Dosage"]
NEGATION_RE = re.compile(r"\b(no|not|never|without|zero|any|didn't|didnt|don't|dont|wasn't|haven't|hasn't|isn't|nothing)\b")
CATEGORY_ORDER = [SE, "Switching Medications", "Cost", WORKED, NOT_WORKED, "Dosage"]
NEGATION_RE = re.compile(r"\b(no|not|never|without|zero|any|didn't|didnt|don't|dont|wasn't|haven't|hasn't|isn't|nothing)\b")
# Dose amounts such as "50 mg" or "0.5mg"; an approximation of the dose extraction used in data cleaning.
DOSE_RE = re.compile(r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|µg|ml|iu|units?)\b")


def norm(s):
    return re.sub(r"[\s\-']", "", s.lower())


def term_pattern(term):
    words = [re.escape(w).replace("'", "'?") for w in re.split(r"[\s\-]+", term) if w]
    return r"[\s\-]*".join(words)


TERM_OF = {}
for category, terms in WATCHLIST.items():
    for term in terms:
        TERM_OF[norm(term)] = (category, term)
ALL_TERMS = sorted({t for ts in WATCHLIST.values() for t in ts}, key=len, reverse=True)
MASTER = re.compile(r"(?<![\w])(" + "|".join(term_pattern(t) for t in ALL_TERMS) + r")(?![\w])")


def kept_terms(path):
    # Terms the notebook kept (found in 20 or more reviews); every term when the file is absent.
    p = Path(path)
    if not p.exists():
        return set(ALL_TERMS)
    f = pd.read_csv(p)
    return set(f.loc[f["kept"].astype(bool), "term"])


def own_condition(term, cond):
    return term in cond or (cond != "unknown" and cond in term) or term in RELATED.get(cond, ())


def scan(text, condition="Unknown", keep=None):
    """Returns one dict per matched term: category counted, term, whether it was negated, and the snippet."""
    t = str(text).lower().replace("’", "'").replace("‘", "'")
    cond = (condition or "Unknown").lower()
    keep = keep if keep is not None else set(ALL_TERMS)
    seen, hits = set(), []
    for m in MASTER.finditer(t):
        category, term = TERM_OF.get(norm(m.group(1)), (None, None))
        if category is None or term in seen or term not in keep:
            continue
        if category == SE and own_condition(term, cond):
            continue
        seen.add(term)
        before = re.split(r"[.!?;,]", t[max(0, m.start() - 40):m.start()])[-1]
        negated = bool(NEGATION_RE.search(" ".join(before.split()[-3:])))
        counted = NOT_WORKED if (category == WORKED and negated) else category
        hits.append({"category": counted, "term": term, "negated": negated,
                     "snippet": text[max(0, m.start() - 40):m.end() + 40]})
    for m in DOSE_RE.finditer(t):
        hits.append({"category": "Dosage", "term": m.group(0), "negated": False, "snippet": text[max(0, m.start() - 40):m.end() + 40]})
    return hits
