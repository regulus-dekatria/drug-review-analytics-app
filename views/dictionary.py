"""Data dictionary: the source columns and the fields the cleaning pipeline adds (text from the original dashboard)."""
import pandas as pd
import streamlit as st

from core import footer
from dash import hero

hero("Data · Data dictionary", "What each field means",
     "The seven columns the source file carries, the known defect in each, and the fields the cleaning notebook adds. "
     "Together they turn 215,063 rows into 130,558 opinions.")

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
]
cfg = {"Field": st.column_config.TextColumn(width="small"), "Type": st.column_config.TextColumn(width="small"),
       "Description": st.column_config.TextColumn(width="large")}
st.markdown("<div class='q'>Source columns</div>", unsafe_allow_html=True)
st.dataframe(pd.DataFrame(SOURCE, columns=["Field", "Type", "Description"]), hide_index=True, width="stretch", column_config=cfg)
st.markdown("<div class='q'>Added by the cleaning pipeline</div>", unsafe_allow_html=True)
st.dataframe(pd.DataFrame(DERIVED, columns=["Field", "Type", "Description"]), hide_index=True, width="stretch", column_config=cfg)
st.caption("The counting basis: counts of medications, conditions and records use all 215,063 records, and every rating "
           "statistic uses the 130,558 distinct reviews.")
footer()
