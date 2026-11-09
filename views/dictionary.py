"""Data dictionary: the source columns and the fields the cleaning pipeline adds (text from the original dashboard)."""
import pandas as pd
import streamlit as st

from dash import box, esc, hero, show

hero("Data Dictionary")

SOURCE = [
    ("uniqueID", "integer", "The identifier the source file assigns to each record. Unique, not sequential."),
    ("drugName", "text", "The medication as Drugs.com recorded it. A brand and its generic are separate names, which is where the mirrored copies come from."),
    ("condition", "text", "What the patient was treating. Carries two defects: labels truncated by one character, and rows where a page fragment landed in the column instead of a condition."),
    ("review", "text", "The free text. Wrapped in one pair of double quotes and holding HTML entities such as &#039; for an apostrophe."),
    ("rating", "integer 1 to 10", "The satisfaction score. Every rating statistic on the dashboard rests on this field."),
    ("date", "date, 07-Mar-2014", "When the review was posted."),
    ("usefulCount", "integer", "How many readers marked the review helpful. Heavily right-skewed."),
]
DERIVED = [
    ("review_clean", "text", "The review with the quote wrapper removed, entities decoded and whitespace collapsed."),
    ("condition_valid", "boolean", "False on the rows where the condition column held a page fragment. Those rows are kept and flagged, never imputed."),
    ("dup_group_id", "integer", "Groups the mirrored copies. The signature is the cleaned text, the date and usefulCount, deliberately excluding drugName."),
    ("is_group_primary", "boolean", "True on one row per group. The de-duplicated view is the rows where this is true, and it is what every rating statistic uses."),
    ("review_date", "date", "The parsed date, plus year, month and quarter."),
    ("rating_band", "category", "Low 1 to 3, Middle 4 to 7, High 8 to 10."),
    ("review_word_count", "integer", "Length of the cleaned text in words."),
    ("is_short_text_repeat", "boolean", "True on very short reviews whose text repeats elsewhere. They are flagged rather than merged, because a short phrase such as \"Works great\" can come from different patients."),
]


def dict_table(rows):
    body = "".join(f"<tr><th scope='row'><code>{esc(f)}</code></th><td>{esc(t)}</td><td>{esc(d)}</td></tr>" for f, t, d in rows)
    return f"<table class='dict'><thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead><tbody>{body}</tbody></table>"


with box("Source Columns", "dict-source", key="source_cols"):
    show(dict_table(SOURCE))
with box("Added by the Cleaning Pipeline", "dict-derived", key="basis"):
    show(dict_table(DERIVED))
