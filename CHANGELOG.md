# Changelog

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
