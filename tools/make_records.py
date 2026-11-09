"""Make data/records.parquet for the Records page from the cleaned dataset (run once, locally).

Usage:  python tools/make_records.py ~/Downloads/reviews_clean.parquet
Keeps only the columns the page shows, so the file in the repository stays small.
"""
import sys
from pathlib import Path

import pandas as pd

COLS = ["uniqueID", "drugName", "condition", "review_clean", "rating", "review_date", "usefulCount",
        "is_group_primary", "condition_valid", "is_short_text_repeat"]
src = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path("reviews_clean.parquet")
df = pd.read_parquet(src, columns=COLS)
for c in ["drugName", "condition"]:
    df[c] = df[c].astype("category")
out = Path(__file__).resolve().parent.parent / "data" / "records.parquet"
df.to_parquet(out, compression="zstd", index=False)
print(f"{len(df):,} records -> {out} ({out.stat().st_size / 1e6:.1f} MB)")
