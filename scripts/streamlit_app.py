import streamlit as st
import pandas as pd
import polars as pl

# Load your movie data
df = pd.read_parquet("./data/movies_df.parquet")

st.title("🎬 My Movie Dashboard")

# Filters
viewed_filter = st.selectbox("liked?", options=["All", True, False])
if viewed_filter != "All":
    df = df[df["liked"] == viewed_filter]

# year_range = st.slider(
#     "year Range", int(df["year"].min()), int(df["year"].max()), (1990, 2025)
# )
# df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])].sort_values(
#     "index", ascending=False
# )

st.dataframe(
    df.sort_values("index", ascending=False)[
        [
            "title",
            "year",
            "director",
            "liked",
        ]
    ]
)
