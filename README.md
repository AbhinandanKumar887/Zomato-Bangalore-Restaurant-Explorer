# Zomato Bangalore Restaurant Explorer

An end-to-end data project on the **Zomato Bangalore** dataset — a cleaned CSV of 51 000+ restaurant listings — featuring a reproducible cleaning pipeline and an interactive Streamlit dashboard.

---

## Dataset

**Source:** Zomato Bangalore Restaurants dataset (Kaggle / public domain).

**File:** `zomato.csv` (raw) → `zomato_cleaned.csv` (produced by `data_cleaning.py`)

### Column reference

| Column | Meaning |
|---|---|
| `url` | Zomato listing URL |
| `address` | Full postal address |
| `name` | Restaurant name |
| `online_order` | Whether the restaurant accepts online orders (`Yes` / `No`) |
| `book_table` | Whether table booking is available (`Yes` / `No`) |
| `rate` | Aggregate customer rating out of 5 (e.g. `4.1/5`) |
| `votes` | Total number of customer votes |
| `phone` | Contact number(s) |
| `location` | Neighbourhood / locality in Bangalore |
| `rest_type` | Type of restaurant (e.g. Casual Dining, Café, Quick Bites) |
| `dish_liked` | Comma-separated list of popular dishes mentioned by reviewers |
| `cuisines` | Comma-separated list of cuisine types served |
| `approx_cost(for two people)` | Approximate cost for two people in INR (₹) |
| `reviews_list` | Raw list of (rating, review-text) tuples scraped from Zomato |
| `menu_item` | Menu items (often empty in public datasets) |
| `listed_in(type)` | Meal category the restaurant is listed under (Buffet, Delivery, etc.) |
| `listed_in(city)` | City area under which the restaurant is listed |

---

## Data Cleaning Summary

Implemented in [`data_cleaning.py`](data_cleaning.py). Run once to produce `zomato_cleaned.csv`.

| Step | Action |
|---|---|
| **Duplicate removal** | Exact duplicate rows dropped (`df.drop_duplicates()`) |
| **Null handling** | Rows with missing `name`, `location`, or `cuisines` dropped; remaining nulls filled with sensible defaults (`"No"`, `0`, `""`) |
| **Rate parsing** | String format `"4.1/5"` → `float 4.1`; values like `"NEW"` or `"-"` → `NaN` |
| **Cost parsing** | Comma-formatted strings (e.g. `"1,200"`) → `int 1200` |
| **Votes parsing** | Coerced to integer; NaN → `0` |
| **Outlier removal** | Ratings outside `[1.0, 5.0]` removed; placeholder `0` ratings dropped |
| **Header standardisation** | All column names lowercased, spaces/slashes → `_`, parentheses removed |
| **Whitespace normalisation** | Leading/trailing whitespace stripped from all string columns |

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Produce the cleaned file (optional — dashboard can also read the raw file)

```bash
python data_cleaning.py
```

### 3. Launch the dashboard

```bash
streamlit run dashboard.py
```

The app opens at **http://localhost:8501** in your browser.

> **Tip:** The dashboard auto-detects `zomato_cleaned.csv` first; if not found it falls back to `zomato.csv`.

---

## Dashboard Features

| Feature | Details |
|---|---|
| **KPI strip** | Total restaurants · Avg rating · Avg votes · Avg cost for two · Unique locations |
| **Rating histogram** | Distribution of ratings across filtered restaurants |
| **Online order pie** | Share of restaurants with / without online ordering |
| **Top 10 locations bar** | Locations with the most restaurants |
| **Top 10 cuisines bar** | Most represented cuisine types |
| **Top rated scatter** | Rating × Votes bubble chart for the best-reviewed restaurants |
| **Cost box plot** | Spread of approximate cost for two people |
| **Restaurant type bar** | Breakdown by dining format |
| **Search + data table** | Free-text search over name / cuisine / location; sortable, scrollable |

**Sidebar filters:** location, cuisine, online order, book table, rating range, max cost.

---

## Folder Structure

```
.
├── zomato.csv               # Raw dataset (input)
├── zomato_cleaned.csv       # Cleaned dataset (output of data_cleaning.py)
├── data_cleaning.py         # Cleaning pipeline (raw → clean)
├── dashboard.py             # Streamlit dashboard
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── .gitignore               # Git ignore rules
```

---

## Requirements

- Python ≥ 3.9
- See [`requirements.txt`](requirements.txt) for package versions
