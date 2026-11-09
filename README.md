# Drug Review Analytics

A Streamlit app that helps pharmacy managers and drug safety teams read patient feedback at scale. Built for the
Analytics Techniques and Tools course at Jose Rizal University on the UCI Drug Review dataset (Drugs.com reviews,
2008 to 2017).

## Pages

| Page | What it does |
|---|---|
| Overview | Headline figures on satisfaction and where feedback sits |
| Volume Analysis, Average Ratings, Rating Dispersion, Rankings | The descriptive dashboard from the prelim and midterm, filtered live by condition, medication and year |
| Predictive Insights | The rating model's calls on the 2016-2017 test reviews, by condition and medication |
| Records | The cleaned table, one row per record, with duplicate copies and unusable conditions kept and marked |
| Data Dictionary | Source and derived fields |
| Classify a Message | Estimates the rating group (Low 1-3, Middle 4-7, High 8-10) of an unrated message with a compressed DistilBERT model, and lists the watchlist topics it mentions. Also classifies a CSV of messages and sorts the likely poor experiences first |
| Predict Helpfulness | Estimates whether a new review will rank in the top 25% of helpful votes among reviews posted in the same month (LightGBM) |
| Reviews Analysis | Sentiment, keyword watchlist, semantic themes and the words that separate low from high ratings, overall or by condition |
| Model Performance | Test results on 2016-2017 reviews, the comparison with a no-skill baseline, and the training logs |

## Repository layout

```
app.py                  entry point and navigation
core.py                 model loading, scoring and styling
watchlist.py            keyword watchlist rules (same as the NLP notebook)
glossary.py             tooltip definitions
dash.py                 shared filters, calculations and charts for the dashboard pages
views/                  one file per page
models/run2/            exported models (from models/run2 in the project Drive)
data/                   summary files from the notebooks
.streamlit/config.toml  theme
requirements.txt        pinned libraries
```

Files copied from the project Drive:

| Drive | Repository |
|---|---|
| `models/run2/` (whole folder) | `models/run2/` |
| `derived/nlp/reviews_analysis.json` | `data/reviews_analysis.json` |
| `derived/nlp/watchlist_term_frequency.csv` | `data/watchlist_term_frequency.csv` |
| `derived/predictive/training_log_run2.json` | `data/training_log_run2.json` |
| `derived/dashboard/overview_cube.parquet` | `data/overview_cube.parquet` |
| `derived/dashboard/overview_meta.json` | `data/overview_meta.json` |
| `derived/dashboard/predictive_cube.parquet` | `data/predictive_cube.parquet` |

## Run locally

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On macOS, LightGBM also needs `brew install libomp`.

## Deploy

Streamlit Community Cloud, Python 3.13 (set under Advanced settings when deploying; it cannot be changed later),
main file `app.py`.

## Limits

English only; the rating group estimates the star rating a patient would give and is not a clinical judgement or
medical advice; helpfulness partly reflects how many readers a medication's page gets. Nothing typed into the app is
stored.

## Records page data

The Records page reads `data/records.parquet`, a slim copy of the cleaned dataset. To make it, download
`reviews_clean.parquet` from the project Drive (derived folder) and run once:

```
python tools/make_records.py ~/Downloads/reviews_clean.parquet
```
