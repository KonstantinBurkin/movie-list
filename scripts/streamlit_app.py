import streamlit as st
import pandas as pd
import collections
import plotly.express as px

# Load your movie data
df = pd.read_parquet("./data/movies_df.parquet")
df = df.loc[df["omdb_id"] != "Not found"]

st.title("🎬 My Movie Dashboard")

# Filters
viewed_filter = st.selectbox("liked?", options=["All", True, False])
if viewed_filter != "All":
    df = df.loc[df["liked"] == viewed_filter]

st.dataframe(
    df.reset_index(drop=True).sort_values("index", ascending=False)[
        [
            "title",
            # "omdb_id",
            "year",
            "director",
            "liked",
            "genre",
            # "actors",
            # "writer",
        ]
    ]
)

st.subheader("📊 Movie Analytics")
# Extract director column, split by comma, and count occurrences
director_list = df["director"].dropna().tolist()
all_directors = []
for d in director_list:
    all_directors.extend([x.strip() for x in d.split(",") if x.strip()])

top_directors = collections.Counter(all_directors).most_common(20)
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
    title="Top 20 Most Common Directors",
    hover_name=directors,
    hover_data={"Movies": hover_text},
)
# Optionally, set custom hovertemplate for better formatting
fig.update_traces(
    hovertemplate="<b>%{y}</b><br>Number of Movies: %{x}<br>Movies:<br>%{customdata[0]}"
)

fig.update_layout(yaxis_title_font_size=14)

st.plotly_chart(fig, width="stretch")

# Extract actor column, split by comma, and count occurrences
actor_list = df["actors"].dropna().tolist()
all_actors = []
for a in actor_list:
    all_actors.extend([x.strip() for x in a.split(",") if x.strip()])

top_actors = collections.Counter(all_actors).most_common(15)
actors, actor_counts = zip(*top_actors)

# Get list of movies for each actor
actor_movies = {
    actor: df[df["actors"].str.contains(actor, na=False)]["title"].tolist()
    for actor in actors
}
actor_hover_text = ["<br>".join(actor_movies[actor]) for actor in actors]

fig_actors = px.bar(
    x=actor_counts,
    y=actors,
    orientation="h",
    labels={"x": "Number of Movies", "y": "Actor"},
    title="Top 15 Most Popular Actors",
    hover_name=actors,
    hover_data={"Movies": actor_hover_text},
)
fig_actors.update_traces(
    hovertemplate="<b>%{y}</b><br>Number of Movies: %{x}<br>Movies:<br>%{customdata[0]}"
)

st.plotly_chart(fig_actors, width="stretch")

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
    title="Top 15 Favorite Genres",
)
st.plotly_chart(fig_genre, width="stretch")


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
st.plotly_chart(fig_years, width="stretch")


# Most expensive movies
expensive_movies = (
    df[~df["box_office"].isna()].sort_values("box_office", ascending=False).head(15)
)

fig_expensive = px.bar(
    expensive_movies,
    x="box_office",
    y="title",
    orientation="h",
    labels={"box_office": "Box Office ($)", "title": "Movie"},
    title="Top 15 Most Grossing Movies (Box Office)",
)
st.plotly_chart(fig_expensive, width="stretch")

# Least expensive movies
cheap_movies = (
    df[~df["box_office"].isna()].sort_values("box_office", ascending=True).head(15)
)

fig_cheap = px.bar(
    cheap_movies,
    x="box_office",
    y="title",
    orientation="h",
    labels={"box_office": "Box Office ($)", "title": "Movie"},
    title="Top 15 Least Grossing Movies (Box Office)",
)
st.plotly_chart(fig_cheap, width="stretch")
