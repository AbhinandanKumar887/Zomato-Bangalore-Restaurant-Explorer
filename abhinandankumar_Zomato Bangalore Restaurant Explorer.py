"""
data_cleaning.py
----------------
Reproduces the full cleaning pipeline:
  raw zomato.csv  →  zomato_cleaned.csv

Steps
-----
1. Load raw CSV
2. Standardise column headers (strip whitespace, lower-snake-case)
3. Drop exact duplicate rows
4. Handle missing values
5. Parse & clean the `rate` column  → numeric float
6. Parse & clean `approx_cost`      → numeric int
7. Clean `votes`                    → numeric int
8. Normalise `online_order` / `book_table` → boolean-like Yes/No
9. Remove rate outliers (keep 1.0–5.0 only)
10. Strip leading/trailing whitespace from all string columns
11. Save cleaned CSV
"""

import re
import pandas as pd

RAW_FILE     = "zomato.csv"
CLEAN_FILE   = "zomato_cleaned.csv"

# ---------------------------------------------------------------------------
# 1. Load
# ---------------------------------------------------------------------------
print(f"[1/9] Loading {RAW_FILE} …")
df = pd.read_csv(RAW_FILE, encoding="utf-8", on_bad_lines="skip")
print(f"      Raw shape: {df.shape}")

# ---------------------------------------------------------------------------
# 2. Standardise headers
# ---------------------------------------------------------------------------
print("[2/9] Standardising column headers …")
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(r"[\s/]+", "_", regex=True)   # spaces & slashes → _
    .str.replace(r"[()]+", "",  regex=True)     # drop parentheses
)
# Friendly rename for cost column
df.rename(columns={"approx_costfor_two_people": "approx_cost_for_two"}, inplace=True)

print(f"      Columns: {list(df.columns)}")

# ---------------------------------------------------------------------------
# 3. Drop exact duplicate rows
# ---------------------------------------------------------------------------
print("[3/9] Removing duplicate rows …")
before = len(df)
df.drop_duplicates(inplace=True)
print(f"      Dropped {before - len(df):,} duplicates  (remaining: {len(df):,})")

# ---------------------------------------------------------------------------
# 4. Handle missing values
# ---------------------------------------------------------------------------
print("[4/9] Handling missing values …")

# Critical columns — drop rows where these are null
critical = ["name", "location", "cuisines"]
df.dropna(subset=critical, inplace=True)

# Non-critical — fill with sensible defaults
df["rate"]               = df["rate"].fillna("0/5")
df["votes"]              = df["votes"].fillna(0)
df["approx_cost_for_two"]= df["approx_cost_for_two"].fillna(0)
df["online_order"]       = df["online_order"].fillna("No")
df["book_table"]         = df["book_table"].fillna("No")
df["rest_type"]          = df["rest_type"].fillna("Unknown")
df["dish_liked"]         = df["dish_liked"].fillna("")
df["menu_item"]          = df["menu_item"].fillna("")
df["phone"]              = df["phone"].fillna("")

print(f"      Shape after null handling: {df.shape}")

# ---------------------------------------------------------------------------
# 5. Parse `rate`  →  numeric float  (e.g. "4.1/5" → 4.1, "NEW" → NaN)
# ---------------------------------------------------------------------------
print("[5/9] Parsing `rate` column …")

def parse_rate(val):
    val = str(val).strip()
    match = re.match(r"^(\d+\.?\d*)\s*/\s*5", val)
    if match:
        return float(match.group(1))
    return float("nan")

df["rate"] = df["rate"].apply(parse_rate)

# ---------------------------------------------------------------------------
# 6. Parse `approx_cost_for_two`  →  numeric int
# ---------------------------------------------------------------------------
print("[6/9] Parsing `approx_cost_for_two` column …")
df["approx_cost_for_two"] = (
    df["approx_cost_for_two"]
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.extract(r"(\d+)")[0]
    .astype(float)
    .fillna(0)
    .astype(int)
)

# ---------------------------------------------------------------------------
# 7. Parse `votes`  →  numeric int
# ---------------------------------------------------------------------------
print("[7/9] Parsing `votes` column …")
df["votes"] = (
    pd.to_numeric(df["votes"], errors="coerce")
    .fillna(0)
    .astype(int)
)

# ---------------------------------------------------------------------------
# 8. Normalise Yes/No columns
# ---------------------------------------------------------------------------
print("[8/9] Normalising Yes/No columns …")
for col in ["online_order", "book_table"]:
    df[col] = df[col].str.strip().str.capitalize()
    df[col] = df[col].where(df[col].isin(["Yes", "No"]), other="No")

# ---------------------------------------------------------------------------
# 9. Remove rate outliers  (valid: 1.0–5.0; drop 0 which was a fill value)
# ---------------------------------------------------------------------------
print("[9/9] Removing rate outliers …")
before = len(df)
df = df[(df["rate"].isna()) | ((df["rate"] >= 1.0) & (df["rate"] <= 5.0))]
print(f"      Dropped {before - len(df):,} outlier rows  (remaining: {len(df):,})")

# Strip whitespace from all object columns
str_cols = df.select_dtypes(include="object").columns
df[str_cols] = df[str_cols].apply(lambda s: s.str.strip())

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
df.to_csv(CLEAN_FILE, index=False, encoding="utf-8")
print(f"\nDone! Cleaned file saved -> {CLEAN_FILE}  ({len(df):,} rows x {df.shape[1]} cols)")
