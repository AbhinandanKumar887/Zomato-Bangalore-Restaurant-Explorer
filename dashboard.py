"""
dashboard.py
------------
Interactive Streamlit dashboard for the Zomato Bangalore dataset.
Run with:  streamlit run dashboard.py
"""

import re
import pandas as pd
import plotly.express as px
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Zomato Bangalore Explorer",
    page_icon="🍽️",
    layout="wide",
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """Load the cleaned CSV and parse types."""
    df = pd.read_csv(path, encoding="utf-8")

    # Ensure rate is numeric (handles both raw and pre-cleaned files)
    if df["rate"].dtype == object:
        def parse_rate(val):
            m = re.match(r"^(\d+\.?\d*)\s*/\s*5", str(val).strip())
            return float(m.group(1)) if m else float("nan")
        df["rate"] = df["rate"].apply(parse_rate)

    # Ensure votes / cost numeric
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)
    cost_col = next((c for c in df.columns if "cost" in c.lower()), None)
    if cost_col:
        df[cost_col] = (
            pd.to_numeric(
                df[cost_col].astype(str).str.replace(",", "", regex=False),
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )
    return df


# ─ Detect cleaned vs raw column names ─────────────────────────────────────────
try:
    df = load_data("zomato_cleaned.csv")
    COST_COL = next((c for c in df.columns if "cost" in c.lower()), None)
except FileNotFoundError:
    df = load_data("zomato.csv")
    # raw file uses original headers
    df.rename(
        columns={
            "approx_cost(for two people)": "approx_cost_for_two",
            "listed_in(type)": "listed_in_type",
            "listed_in(city)": "listed_in_city",
        },
        inplace=True,
    )
    COST_COL = "approx_cost_for_two"

COST_COL = COST_COL or "approx_cost_for_two"

# ── Sidebar filters ───────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

all_locations = sorted(df["location"].dropna().unique())
sel_locations = st.sidebar.multiselect(
    "Location(s)",
    options=all_locations,
    default=[],
    placeholder="All locations",
)

all_cuisines = sorted(
    {c.strip() for row in df["cuisines"].dropna() for c in str(row).split(",")}
)
sel_cuisines = st.sidebar.multiselect(
    "Cuisine(s)",
    options=all_cuisines,
    default=[],
    placeholder="All cuisines",
)

online_opt = st.sidebar.radio("Online Order", ["All", "Yes", "No"], horizontal=True)
book_opt   = st.sidebar.radio("Book Table",   ["All", "Yes", "No"], horizontal=True)

min_rate, max_rate = st.sidebar.slider(
    "Rating range", min_value=1.0, max_value=5.0, value=(1.0, 5.0), step=0.1
)

cost_max = int(df[COST_COL].max()) if df[COST_COL].max() > 0 else 6000
max_cost = st.sidebar.slider(
    "Max cost for two (₹)", min_value=0, max_value=cost_max, value=cost_max, step=100
)

# ── Apply filters ─────────────────────────────────────────────────────────────
fdf = df.copy()

if sel_locations:
    fdf = fdf[fdf["location"].isin(sel_locations)]

if sel_cuisines:
    pattern = "|".join(re.escape(c) for c in sel_cuisines)
    fdf = fdf[fdf["cuisines"].str.contains(pattern, case=False, na=False)]

if online_opt != "All":
    fdf = fdf[fdf["online_order"].str.strip().str.capitalize() == online_opt]

if book_opt != "All":
    fdf = fdf[fdf["book_table"].str.strip().str.capitalize() == book_opt]

fdf = fdf[fdf["rate"].between(min_rate, max_rate, inclusive="both") | fdf["rate"].isna()]
fdf = fdf[fdf[COST_COL] <= max_cost]

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("🍽️ Zomato Bangalore Restaurant Explorer")
st.caption(
    f"Showing **{len(fdf):,}** restaurants out of **{len(df):,}** total after applying filters."
)

st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
rated = fdf.dropna(subset=["rate"])

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("🍴 Total Restaurants",  f"{len(fdf):,}")
k2.metric("⭐ Avg Rating",          f"{rated['rate'].mean():.2f}" if len(rated) else "—")
k3.metric("🗳️ Avg Votes",           f"{fdf['votes'].mean():,.0f}" if len(fdf) else "—")
k4.metric("💰 Avg Cost for Two",    f"₹{fdf[COST_COL].replace(0, pd.NA).dropna().mean():,.0f}" if len(fdf) else "—")
k5.metric("📍 Unique Locations",    fdf["location"].nunique())

st.divider()

# ── Row 1: Rating distribution + Online-order pie ─────────────────────────────
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Rating Distribution")
    if len(rated):
        fig_hist = px.histogram(
            rated,
            x="rate",
            nbins=20,
            color_discrete_sequence=["#e23744"],
            labels={"rate": "Rating", "count": "Restaurants"},
        )
        fig_hist.update_layout(
            margin=dict(t=20, b=20),
            plot_bgcolor="white",
            bargap=0.05,
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No rated restaurants match current filters.")

with col2:
    st.subheader("Online Order Availability")
    oo_counts = fdf["online_order"].value_counts().reset_index()
    oo_counts.columns = ["online_order", "count"]
    fig_pie = px.pie(
        oo_counts,
        names="online_order",
        values="count",
        color_discrete_sequence=["#e23744", "#f5a623"],
        hole=0.45,
    )
    fig_pie.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Row 2: Top 10 locations + Top 10 cuisines ────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Top 10 Locations by Restaurant Count")
    top_loc = (
        fdf["location"].value_counts().head(10).reset_index()
    )
    top_loc.columns = ["location", "count"]
    fig_loc = px.bar(
        top_loc,
        x="count",
        y="location",
        orientation="h",
        color="count",
        color_continuous_scale="Reds",
        labels={"count": "Restaurants", "location": ""},
    )
    fig_loc.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin=dict(t=20, b=20),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_loc, use_container_width=True)

with col4:
    st.subheader("Top 10 Cuisines")
    cuisine_series = (
        fdf["cuisines"]
        .dropna()
        .str.split(",")
        .explode()
        .str.strip()
    )
    top_cui = cuisine_series.value_counts().head(10).reset_index()
    top_cui.columns = ["cuisine", "count"]
    fig_cui = px.bar(
        top_cui,
        x="count",
        y="cuisine",
        orientation="h",
        color="count",
        color_continuous_scale="Oranges",
        labels={"count": "Restaurants", "cuisine": ""},
    )
    fig_cui.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin=dict(t=20, b=20),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_cui, use_container_width=True)

# ── Row 3: Top-rated restaurants + Cost distribution ─────────────────────────
col5, col6 = st.columns([3, 2])

with col5:
    st.subheader("Top 10 Restaurants by Rating × Votes")
    top_rest = (
        rated[rated["votes"] >= 50]
        .sort_values(["rate", "votes"], ascending=False)
        .head(10)[["name", "location", "cuisines", "rate", "votes", COST_COL]]
        .reset_index(drop=True)
    )
    top_rest.index += 1

    if len(top_rest):
        fig_top = px.scatter(
            top_rest,
            x="votes",
            y="rate",
            size="votes",
            color="rate",
            hover_name="name",
            hover_data={"location": True, "cuisines": True, COST_COL: True},
            color_continuous_scale="RdYlGn",
            size_max=40,
            labels={"votes": "Votes", "rate": "Rating"},
        )
        fig_top.update_layout(margin=dict(t=20, b=20), coloraxis_showscale=False)
        st.plotly_chart(fig_top, use_container_width=True)
    else:
        st.info("Not enough data for this chart with current filters.")

with col6:
    st.subheader("Cost Distribution (₹ for Two)")
    cost_nz = fdf[fdf[COST_COL] > 0][COST_COL]
    if len(cost_nz):
        fig_cost = px.box(
            cost_nz.rename("Cost for Two"),
            color_discrete_sequence=["#e23744"],
            labels={"value": "₹"},
        )
        fig_cost.update_layout(margin=dict(t=20, b=20), showlegend=False)
        st.plotly_chart(fig_cost, use_container_width=True)
    else:
        st.info("No cost data available.")

# ── Row 4: Restaurant type breakdown ─────────────────────────────────────────
st.subheader("Restaurant Type Breakdown")
rest_type_counts = (
    fdf["rest_type"]
    .dropna()
    .str.split(",")
    .explode()
    .str.strip()
    .value_counts()
    .head(12)
    .reset_index()
)
rest_type_counts.columns = ["rest_type", "count"]
fig_rt = px.bar(
    rest_type_counts,
    x="rest_type",
    y="count",
    color="count",
    color_continuous_scale="Blues",
    labels={"rest_type": "Restaurant Type", "count": "Count"},
)
fig_rt.update_layout(margin=dict(t=20, b=20), coloraxis_showscale=False)
st.plotly_chart(fig_rt, use_container_width=True)

# ── Row 5: Searchable data table ──────────────────────────────────────────────
st.divider()
st.subheader("📋 Searchable Restaurant Table")

search_term = st.text_input("Search by name, cuisine or location", placeholder="e.g. Pizza, BTM, Biryani …")

display_df = fdf.copy()
if search_term.strip():
    mask = (
        display_df["name"].str.contains(search_term, case=False, na=False)
        | display_df["cuisines"].str.contains(search_term, case=False, na=False)
        | display_df["location"].str.contains(search_term, case=False, na=False)
    )
    display_df = display_df[mask]

TABLE_COLS = [
    c for c in ["name", "location", "rest_type", "cuisines", "rate", "votes",
                COST_COL, "online_order", "book_table"]
    if c in display_df.columns
]

st.dataframe(
    display_df[TABLE_COLS].sort_values("rate", ascending=False).reset_index(drop=True),
    use_container_width=True,
    height=450,
)

st.caption(f"Showing {len(display_df):,} records")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<hr style='margin-top:2rem'><p style='text-align:center;color:grey;font-size:0.8rem'>"
    "Data source: Zomato Bangalore dataset · Built with Streamlit & Plotly</p>",
    unsafe_allow_html=True,
)
