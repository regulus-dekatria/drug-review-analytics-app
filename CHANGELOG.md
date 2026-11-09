# Changelog

## 0.5.0 (2026-11-09)
### Added
- Overview: Reviews Analysis and Predictive Insights summary panels (tone of wording, wording matching the rating, most mentioned topic; actual against flagged Low, Low found in the top 20%, condition to review first), each linking to its full page
- Predictive Insights: the table gets search, sort (Most reviews, Highest chance of Low, Largest gap, Most helpful), minimum reviews and clickable rows; Conditions to Review First gets a Minimum reviews control
- Data Dictionary: `is_short_text_repeat`, the flag the Records page uses
### Changed
- Hover details on every bar, dot and segment use the navy box of the info tooltips instead of the browser's grey one
- Reviews Analysis: topic names in title case in the chart and its note; theme bars use the app's scheme (largest navy, the rest blue); repeated words merged in theme names ("Migraines · Pressure")
- Data Dictionary: descriptions wrap in full instead of being cut off
- Predictive Insights panels moved onto the shared panel design
### Fixed
- The Topics Mentioned note claimed other medications named in reviews were "often one the patient switched from"; the data shows only that one is named, so the claim is removed

## 0.4.0 (2026-11-09)
### Restored from the checked dashboard
Every visual from the prelim and midterm dashboard is back, under its original title, in the original order on each page. Newer panels follow them.
- Overview: the ten KPI cards in two rows; Top 10 Conditions by Volume and Top 10 Medications by Volume
- Volume Analysis: Rating Distribution with the Chart and Table toggle; Volume Concentration with the Medications and Conditions toggle and the original bands (1, 2, 3-5, 6-10, 11-30, 31-100, 100+)
- Average Ratings: Rating Scores Distribution with three marked lines (mean, median, mode); How Medications for Each Condition Are Rated as centred bars for every condition in a scrolling panel, with search, sort and minimum; Rating Scores by Condition Treated with its original columns
- Rating Dispersion: Medications Patients Agree On, and Medications They Do Not as a dot plot with search, sort and minimum; Where Reviews Sit at the Extremes as centred bars with search and five sorts, including Least polarised
- Rankings: the ladder with nine rungs; Medications by Rank with its original columns (Distribution, Reviews, Average, Rank, Rated 8+) plus a Position column
- Records page: the cleaned table with KPI cards, defect filters (mirrored copies, no usable condition, short-text repeats), text search, sorting and paging (`data/records.parquet`, made once with `tools/make_records.py`)
- Filters: Ratings filter, year presets (All time, 2008 to 2012, 2013 to 2017, 2016 to 2017), removable chips for each active filter and Reset all
- Hover details on every bar; clicking a table row or a Rankings dot filters the dashboard to that condition or medication
- Controls look the same everywhere: search, sort and minimum sit in the panel header on the right; view switches are segmented buttons
### Changed
- Page headers show only the page name in title case; Overview is titled Patient Drug Reviews. The line above each title and the subtitle are gone
- New panels use short title-case labels (for example Topics Mentioned, Review Themes); original panels keep their original titles; the "Business question" label is removed
- Sidebar names and every heading, tab and expander label in title case (Classify a Message, Predict Helpfulness, Models and Data, Model Performance, Data Dictionary); all sidebar sections stay open
- Panels sit in balanced rows: paired panels share one height with their notes aligned along the bottom, and uneven pairs take a full row
- Tables, the Rankings scatter and the training-log charts sit in the same cards as the HTML charts; Plotly charts use the app's fonts and colours
- Reviews Analysis rebuilt on the shared cards and bars: topics sorted largest first, a Neutral Wording card so the three tone shares add to 100%, theme labels in title case
- Rating Dispersion: Most Divided and Most Agreed panels added after the original visuals
- Predictive Insights opens with a Reviews Checked card; the scope caption is now a tooltip
- Compact inline controls (segmented buttons, narrow inputs) replace full-width dropdowns on Average Ratings, Rating Dispersion, Rankings and Reviews Analysis
- Notes and tooltips rewritten for pharmacy managers; method terms (VADER, NPMI, ARI, kappa) moved to Model Performance under Review Text Analysis Checks
- Card numbers set in bold on every page; Model Performance and the Predict pages use the same KPI cards
- Average Ratings: the chart and the table each have their own search, sort and minimum controls
- Reviews Analysis: Words in Low and High Ratings shown as two word clouds sized by rank (low in navy, high in aqua on navy); Most Mentioned Terms shown as a table of five terms per topic, most used first, with review counts and bars
- Classify a Message and Predict Helpfulness show a visible line under each result: estimates from patient wording, not medical advice
### Removed
- Footer line on every page
- About page and its sidebar entry; its content moves to the project documentation. The app carries no author name
- Scope lines and captions that only counted or commented under charts and tables
- The How These Figures Are Counted section on Overview; the counting rules belong in the project documentation
### Fixed
- Percentages in tables and bar labels showed varying decimals (50.2%, 45.03%, 35%); all now show one decimal
- Counts in tables had no thousands separator (19579); all now show 19,579
- Word clouds are balanced line by line, with the largest words centred
- Actually Helpful on Predictive Insights explains why high-volume conditions such as Birth Control show low shares
- Condition labels that are page fragments (starting mid-word, such as "moterol)") are grouped under Condition not recorded
- Terms in Effectiveness: did not work that were caught after a negation show with it ("no relief", "not helped")
- Scrolled content showed through the Streamlit Cloud toolbar; the header is now solid and the page starts below it

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
