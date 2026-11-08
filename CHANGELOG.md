# Changelog

## 0.3.0 (2026-11-09)
### Added
- The full dashboard: Volume Analysis, Average Ratings, Rating Dispersion and Rankings rebuilt from the prelim and midterm dashboard, on the same counting rules (volume on all records, opinions on distinct reviews)
- Predictive Insights page: the rating model's calls on the 2016-2017 test reviews by condition and medication, and where it would send the team first (`data/predictive_cube.parquet`)
- Data dictionary page with the original source and derived field descriptions
- Sidebar filters (Condition, Medication, Years) shared by every dashboard page, with a reset button
- Hero headers on every page; About shows model versions as a table
### Changed
- Design: gradients removed; flat palette colours with a dot texture, layered shadows and fine highlights
- Pattern textures from the analyst report, each with a meaning: navy hatching for comparison series and averages below the ranking threshold, light cyan hatching for reference quantities (all other, the middle of the scale), cyan dots for empty states and the smallest group; hero band with a cyan rule
- Review insights renamed Reviews Analysis, following the condition filter where it has its own analysis
- Data files reload when replaced, without restarting the app
### Fixed
- Tooltip text containing an apostrophe broke its layout

## 0.2.0 (2026-11-09)
### Added
- Overview page (default): hero band, four KPI cards and four visuals headed by their business questions, with conclusion notes written from the data; Condition, Medication and Year filters recalculate everything from the summary table built in Notebook 3 (`data/overview_cube.parquet`, `data/overview_meta.json`)
- Tooltips on every KPI and chart, using the definitions from the original dashboard notebook (`glossary.py`)
- Design layer adapted from the AURA capstone: colour roles as CSS variables, dot texture and soft gradients over the palette, gradient hero, layered card shadows with a gradient top edge, hover lift, inset accent bars, 2px focus outlines, tabular figures
- Motion: page rise, card pop, bars and columns that grow in, all off under reduced motion and in print
- Author line on the About page and in the footer
### Changed
- Navigation grouped as Dashboard, Predict and Models; Material Symbols Rounded used for every icon

## 0.1.1 (2026-11-09)
### Fixed
- Sidebar and expander icons rendered as text because the body font rule overrode the icon font
- Theme caption counted ten themes when the data holds fewer
### Changed
- Helpfulness page explains that leaving condition or medication at Unknown lowers the estimate
- Performance page states that headline figures come from the full DistilBERT on all test reviews, with the compressed copy checked on a sample
- metrics.json re-exported with six decimals so rounded figures match the notebook (severe errors 2.7%)

## 0.1.0 (2026-11-08)
### Added
- Classify a message: compressed DistilBERT (ONNX, 8-bit) with TF-IDF fallback, watchlist topics with negation marking, comparison with the word-based model, session test log with CSV download, and CSV batch classification sorted by likelihood of a poor experience
- Predict helpfulness: LightGBM on rating, length, condition and medication, with score bands against 2016-2017 reviews
- Review insights: sentiment, watchlist, themes and word comparison by condition from the NLP notebook
- Model performance: test results, baseline comparison, training logs and the compressed-model check
- About page, footer with model run and served models, Digital Health theme and fonts
