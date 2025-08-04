import streamlit as st
import pandas as pd
import collections
import plotly.express as px

# Load your movie data
df = pd.read_parquet("./data/movies_df.parquet")

st.title("🎬 My Movie Dashboard")

# Filters
viewed_filter = st.selectbox("liked?", options=["All", True, False])
if viewed_filter != "All":
    df = df[df["liked"] == viewed_filter]

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

# Extract director column, split by comma, and count occurrences
director_list = df["director"].dropna().tolist()
all_directors = []
for d in director_list:
    all_directors.extend([x.strip() for x in d.split(",") if x.strip()])

top_directors = collections.Counter(all_directors).most_common(15)
directors, counts = zip(*top_directors)

# Get list of movies for each director
director_movies = {
    director: df[df["director"].str.contains(director, na=False)]["title"].tolist()
    for director in directors
}
hover_text = ["<br>".join(director_movies[director]) for director in directors]

fig = px.bar(
    x=counts,
    y=directors,
    orientation="h",
    labels={"x": "Number of Movies", "y": "Director"},
    title="Top 15 Most Common Directors",
    hover_name=directors,
    hover_data={"Movies": hover_text},
)
# Optionally, set custom hovertemplate for better formatting
fig.update_traces(
    hovertemplate="<b>%{y}</b><br>Number of Movies: %{x}<br>Movies:<br>%{customdata[0]}"
)

st.plotly_chart(fig, use_container_width=True)


# Extract genre column, split by comma, and count occurrences
genre_list = df["genre"].dropna().tolist()
all_genres = []
for g in genre_list:
    all_genres.extend([x.strip() for x in g.split(",") if x.strip()])

top_genres = collections.Counter(all_genres).most_common(15)
genres, genre_counts = zip(*top_genres)

fig_genre = px.bar(
    x=genre_counts,
    y=genres,
    orientation="h",
    labels={"x": "Number of Movies", "y": "Genre"},
    title="Top 15 Most Common Genres",
)
st.plotly_chart(fig_genre, use_container_width=True)


years = df["year"].dropna().tolist()
fig_years = px.histogram(
    x=years,
    nbins=40,
    # histnorm="probability density",
    labels={"x": "Year", "y": "Density"},
    title="Distribution of Movie Release Years",
)
fig_years.update_traces(marker_color="green", opacity=0.6)
fig_years.update_layout(yaxis_title="Density", xaxis_title="Year", bargap=0.05)
st.plotly_chart(fig_years, use_container_width=True)
