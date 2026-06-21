import collections
import json
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================================
# AUTHENTICATION
# ============================================================================
def check_authentication():
    """Check if user is authenticated."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        with st.sidebar:
            st.header("🔐 Authentication")
            password = st.text_input("Enter password:", type="password")
            if st.button("Login"):
                # Get password from secrets or environment
                correct_password = st.secrets.get("APP_PASSWORD", "changeme")
                if password == correct_password:
                    st.session_state.authenticated = True
                    st.success("✅ Authenticated!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password")

    return st.session_state.authenticated


# ============================================================================
# GIT OPERATIONS
# ============================================================================
def create_and_push_movie_branch(movie_title, movie_year):
    """Create a new branch, commit movie data, push to GitHub, and create PR."""
    try:
        # Generate branch name
        safe_title = "".join(c if c.isalnum() else "-" for c in movie_title.lower())
        branch_name = f"add-movie-{safe_title}-{movie_year}"

        # Create and checkout new branch
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            check=True,
            capture_output=True,
        )

        # Add the parquet file
        subprocess.run(
            ["git", "add", "data/movies_df.parquet"],
            check=True,
            capture_output=True,
        )

        # Commit
        commit_msg = f"Add movie: {movie_title} ({movie_year})"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
            capture_output=True,
        )

        # Push to remote
        subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            check=True,
            capture_output=True,
        )

        # Create PR using GitHub CLI
        pr_title = f"Add movie: {movie_title} ({movie_year})"
        pr_body = (
            f"Automatically adding movie via Streamlit app.\n\n**Movie:** {movie_title}"
        )

        result = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                pr_title,
                "--body",
                pr_body,
                "--base",
                "main",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        pr_url = result.stdout.strip()

        # Auto-merge the PR
        subprocess.run(
            ["gh", "pr", "merge", pr_url, "--merge", "--auto"],
            check=True,
            capture_output=True,
        )

        # Switch back to main
        subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)

        return True, pr_url
    except subprocess.CalledProcessError as e:
        # Switch back to main on error
        subprocess.run(["git", "checkout", "main"], capture_output=True)
        return False, str(e)


# Load your movie data
df = pd.read_parquet("./data/movies_df.parquet")
df = df.loc[df["omdb_id"] != "Not found"]

# Check authentication
is_authenticated = check_authentication()

st.title("🎬 My Movie Dashboard")

# Show authentication status
if is_authenticated:
    with st.sidebar:
        st.success("✅ Authenticated")
        st.caption("Movies will be auto-pushed to GitHub")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
else:
    st.info("ℹ️ Login to enable automatic GitHub sync")
# st.header("📚 My Movies")

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


# ============================================================================
# ADD NEW MOVIE SECTION
# ============================================================================
st.header("➕ Add New Movie")

with st.form("add_movie_form"):
    col1, col2 = st.columns([3, 1])

    with col1:
        omdb_id_input = st.text_input(
            "OMDB ID (e.g., tt0111161 for The Shawshank Redemption)",
            placeholder="tt0111161",
        )

    with col2:
        liked_input = st.checkbox("Liked", value=True)

    submit_button = st.form_submit_button("Add Movie")

    if submit_button and omdb_id_input:
        try:
            import re

            import polars as pl
            import requests

            # Extract IMDb ID from input (handle both "tt1234567" and "1234567")
            imdb_id = omdb_id_input.strip()
            if not imdb_id.startswith("tt"):
                imdb_id = f"tt{imdb_id}"

            # Fetch movie details from OMDB API
            with st.spinner("Fetching movie details from OMDB..."):
                omdb_api_key = st.secrets.get("OMDB_API_KEY")
                if not omdb_api_key:
                    st.error("❌ OMDB_API_KEY not found in secrets")
                else:
                    url = f"http://www.omdbapi.com/?apikey={omdb_api_key}&i={requests.utils.quote(imdb_id)}"
                    response = requests.get(url)
                    movie_data = response.json()

                    if movie_data.get("Response") != "True":
                        st.error(f"❌ Movie with OMDB ID '{imdb_id}' not found")
                    else:
                        # Load existing data using polars
                        existing_df = pl.read_parquet("./data/movies_df.parquet")

                        # Check if movie already exists
                        if imdb_id in existing_df["omdb_id"].to_list():
                            st.warning(
                                f"⚠️ Movie '{movie_data['Title']}' already exists in your database!"
                            )
                        else:
                            # Parse box office
                            box_office = None
                            if movie_data.get("BoxOffice") != "N/A":
                                try:
                                    box_office = int(
                                        re.sub(r"[^\d]", "", movie_data["BoxOffice"])
                                    )
                                except Exception:
                                    box_office = None

                            # Parse year
                            year = None
                            if movie_data.get("Year") != "N/A":
                                try:
                                    year = int(movie_data["Year"])
                                except Exception:
                                    year = None

                            # Parse IMDb rating
                            imdb_rating = None
                            if movie_data.get("imdbRating") != "N/A":
                                try:
                                    imdb_rating = float(movie_data["imdbRating"])
                                except Exception:
                                    imdb_rating = None

                            # Create new row matching the notebook structure
                            new_row = {
                                "index": existing_df["index"].max() + 1,
                                "title": movie_data.get("Title", "Unknown"),
                                "year": year,
                                "viewed": datetime.today().date(),
                                "omdb_id": imdb_id,
                                "liked": liked_input,
                                "genre": movie_data.get("Genre", "N/A"),
                                "director": movie_data.get("Director", "Unknown"),
                                "country": movie_data.get("Country", "N/A"),
                                "actors": movie_data.get("Actors", "N/A"),
                                "box_office": box_office,
                                "writer": movie_data.get("Writer", "Unknown"),
                                "language": movie_data.get("Language", "N/A"),
                                "imdb_rating": imdb_rating,
                            }

                            # Create single-row DataFrame and cast to match schema
                            new_row_df = pl.DataFrame([new_row])
                            new_row_df = new_row_df.cast(existing_df.schema)

                            # Concatenate
                            new_df = pl.concat(
                                [existing_df, new_row_df], how="vertical"
                            )

                            # Save to parquet
                            new_df.write_parquet("./data/movies_df.parquet")

                            # If authenticated, push to GitHub
                            if is_authenticated:
                                st.info("📤 Pushing to GitHub...")
                                success, result = create_and_push_movie_branch(
                                    movie_data["Title"], new_row["year"]
                                )
                                if success:
                                    st.success(
                                        f"✅ Successfully added '{movie_data['Title']}' ({new_row['year']})!"
                                    )
                                    st.success(
                                        f"🔗 PR created and auto-merged: {result}"
                                    )
                                else:
                                    st.warning(
                                        f"✅ Movie added locally, but GitHub push failed: {result}"
                                    )
                            else:
                                st.success(
                                    f"✅ Successfully added '{movie_data['Title']}' ({new_row['year']})!"
                                )
                                st.info("💡 Login to automatically sync with GitHub")

                            st.info("🔄 Refreshing page...")
                            st.rerun()

        except Exception as e:
            st.error(f"❌ Error adding movie: {e}")
            st.info("Make sure OMDB_API_KEY is configured in secrets.")

st.divider()

# ============================================================================
# WATCHED MOVIES TABLE
# ============================================================================
# ============================================================================
# RECOMMENDATIONS SECTION
# ============================================================================
st.divider()
st.header("🎯 Recommended Movies")

# Load latest recommendations
recommendations_path = Path("./data/recommendations/recommendations_latest.json")

# Auto-generate recommendations if they don't exist (for Streamlit Cloud)
if not recommendations_path.exists():
    st.info("🔄 Generating recommendations for the first time...")
    try:
        import sys

        sys.path.append(str(Path(__file__).parent))
        from generate_recommendations import generate_recommendations  # noqa: E402

        with st.spinner("Analyzing your movie preferences..."):
            recommendations_list = generate_recommendations(
                retrain=True,
                top_n=5,
                months_back=6,
            )
            if recommendations_list:
                st.success("✅ Recommendations generated successfully!")
                st.rerun()
    except Exception as e:
        st.error(f"Failed to generate recommendations: {e}")
        st.info("Please check that TMDB_API_KEY is configured in Streamlit secrets.")

if recommendations_path.exists():
    try:
        with open(recommendations_path, "r") as f:
            rec_data = json.load(f)

        recommendations = rec_data.get("recommendations", [])
        generated_at = rec_data.get("generated_at", "Unknown")

        if recommendations:
            # Parse timestamp
            try:
                gen_time = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                time_str = gen_time.strftime("%B %d, %Y at %I:%M %p")
            except Exception:
                time_str = generated_at

            st.caption(f"Generated on {time_str}")

            # Display recommendations in a nice format
            for i, rec in enumerate(recommendations, 1):
                with st.container():
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.subheader(f"{i}. {rec['title']} ({rec['year']})")

                        # Create columns for metadata
                        meta_col1, meta_col2, meta_col3 = st.columns(3)

                        with meta_col1:
                            if rec.get("rating"):
                                st.metric("Rating", f"{rec['rating']:.1f}/10")
                            else:
                                st.metric("Rating", "N/A")

                        with meta_col2:
                            st.metric("Match Score", f"{rec['score']:.1f}")

                        with meta_col3:
                            st.metric("Year", rec["year"])

                        # Description
                        if rec.get("overview"):
                            with st.expander("📝 Description", expanded=(i == 1)):
                                st.write(rec["overview"])

                    with col2:
                        # Display poster if available
                        if rec.get("poster_path"):
                            poster_url = (
                                f"https://image.tmdb.org/t/p/w300{rec['poster_path']}"
                            )
                            st.image(poster_url, use_container_width=True)
                        else:
                            st.info("No poster available")

                    st.divider()

        else:
            st.info("No recommendations available yet. Run the recommendation system!")
            with st.expander("🚀 How to generate recommendations"):
                st.code(
                    """
# Generate recommendations
python scripts/generate_recommendations.py

# Or generate more recommendations
python scripts/generate_recommendations.py --top-n 10
                """,
                    language="bash",
                )

    except Exception as e:
        st.error(f"Error loading recommendations: {e}")
        st.info("Please ensure the recommendation system has been run at least once.")
else:
    st.warning("⚠️ No recommendations found")
    st.info("""
    Recommendations will appear here once generated. To create recommendations:

    1. Ensure your TMDB API key is configured in `.env`
    2. Run: `python scripts/generate_recommendations.py`
    3. Reload this page
    """)

st.divider()

# ============================================================================
# ANALYTICS SECTION
# ============================================================================
st.header("📊 Movie Analytics")
# Extract director column, split by comma, and count occurrences
director_list = df["director"].dropna().tolist()
all_directors = []
for d in director_list:
    all_directors.extend([x.strip() for x in d.split(",") if x.strip()])

top_directors = collections.Counter(all_directors).most_common(25)
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
    height=600,
    orientation="h",
    labels={"x": "Number of Movies", "y": "Director"},
    title="Top 25 Most Common Directors",
    hover_name=directors,
    hover_data={"Movies": hover_text},
)
# Optionally, set custom hovertemplate for better formatting
fig.update_traces(
    hovertemplate="<b>%{y}</b><br>Number of Movies: %{x}<br>Movies:<br>%{customdata[0]}"
)

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
