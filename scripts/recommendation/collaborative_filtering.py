"""Collaborative filtering recommendation model using matrix factorization."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import polars as pl  # noqa: E402
import numpy as np  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402
from typing import List, Dict, Tuple  # noqa: E402
import pickle  # noqa: E402
from collections import defaultdict  # noqa: E402
from tmdb_client import TMDBClient  # noqa: E402


class CollaborativeFilteringModel:
    """Item-based collaborative filtering using cosine similarity."""

    def __init__(self, data_path: str = "data/movies_df.parquet"):
        """Initialize the model with movie data."""
        self.data_path = data_path
        self.movies_df = None
        self.recent_movies = None
        self.item_similarity_matrix = None
        self.movie_features = None
        self.tmdb_client = TMDBClient()
        self.model_path = Path("models/cf_model.pkl")

    def load_data(self, months_back: int = 6):
        """Load and filter movies watched in the last N months."""
        self.movies_df = pl.read_parquet(self.data_path)

        cutoff_date = datetime.now().date() - timedelta(days=months_back * 30)

        self.recent_movies = self.movies_df.filter(
            (pl.col("viewed").is_not_null()) & (pl.col("viewed") >= cutoff_date) & (pl.col("liked"))
        )

        print(f"Loaded {len(self.movies_df)} total movies")
        print(f"Using {len(self.recent_movies)} movies from last {months_back} months")

        return self.recent_movies

    def extract_features(self) -> Dict:
        """Extract features from watched movies for similarity computation."""
        features = {
            "genres": defaultdict(int),
            "directors": defaultdict(int),
            "actors": defaultdict(int),
            "years": [],
            "ratings": [],
            "tmdb_ids": [],
        }

        for row in self.recent_movies.iter_rows(named=True):
            if row["genre"]:
                for genre in str(row["genre"]).split(","):
                    genre = genre.strip()
                    features["genres"][genre] += 1

            if row["director"]:
                for director in str(row["director"]).split(","):
                    director = director.strip()
                    features["directors"][director] += 1

            if row["actors"]:
                for actor in str(row["actors"]).split(",")[:3]:
                    actor = actor.strip()
                    features["actors"][actor] += 1

            if row["year"]:
                features["years"].append(row["year"])

            if row["imdb_rating"]:
                features["ratings"].append(row["imdb_rating"])

            if row.get("omdb_id"):
                features["tmdb_ids"].append(row["omdb_id"])

        features["genres"] = dict(features["genres"])
        features["directors"] = dict(features["directors"])
        features["actors"] = dict(features["actors"])

        self.movie_features = features
        return features

    def build_genre_profile(self) -> List[int]:
        """Build a genre preference profile based on watched movies."""
        from tmdb_client import GENRE_MAP

        genre_scores = defaultdict(float)

        for row in self.recent_movies.iter_rows(named=True):
            if row["genre"]:
                rating_weight = row["imdb_rating"] if row["imdb_rating"] else 7.0
                for genre in str(row["genre"]).split(","):
                    genre = genre.strip()
                    genre_scores[genre] += rating_weight

        top_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)[:5]

        genre_ids = []
        for genre_name, _ in top_genres:
            for tmdb_genre, tmdb_id in GENRE_MAP.items():
                if genre_name.lower() in tmdb_genre.lower() or tmdb_genre.lower() in genre_name.lower():
                    genre_ids.append(tmdb_id)
                    break

        return list(set(genre_ids))[:3]

    def get_candidate_movies(self) -> List[Dict]:
        """Fetch candidate movies from TMDB based on user preferences."""
        candidates = []
        watched_titles = set(self.movies_df["title"].to_list())

        genre_ids = self.build_genre_profile()
        print(f"Top genres: {genre_ids}")

        if genre_ids:
            genre_movies = self.tmdb_client.discover_by_genres(genre_ids, min_rating=7.0, limit=30)
            candidates.extend(genre_movies)

        popular_recent = self.tmdb_client.discover_popular_recent(min_year=2020, limit=30)
        candidates.extend(popular_recent)

        for row in self.recent_movies.head(10).iter_rows(named=True):
            if row["imdb_rating"] and row["imdb_rating"] >= 7.5:
                similar = self.tmdb_client.get_movie_by_title(row["title"], row.get("year"))
                if similar and similar.get("tmdb_id"):
                    similar_movies = self.tmdb_client.get_similar_movies(similar["tmdb_id"], limit=10)
                    candidates.extend(similar_movies)

        unique_candidates = []
        seen_ids = set()

        for movie in candidates:
            if movie["tmdb_id"] not in seen_ids and movie["title"] not in watched_titles:
                seen_ids.add(movie["tmdb_id"])
                unique_candidates.append(movie)

        print(f"Found {len(unique_candidates)} candidate movies")
        return unique_candidates

    def compute_similarity_scores(self, candidates: List[Dict]) -> List[Tuple[Dict, float]]:
        """Compute similarity scores for candidate movies."""
        scored_movies = []

        user_genre_counts = defaultdict(int)
        for row in self.recent_movies.iter_rows(named=True):
            if row["genre"]:
                for genre in str(row["genre"]).split(","):
                    user_genre_counts[genre.strip()] += 1

        avg_rating = self.recent_movies["imdb_rating"].mean() if len(self.recent_movies) > 0 else 7.0
        avg_year = int(np.mean(self.movie_features["years"])) if self.movie_features["years"] else 2020

        for movie in candidates:
            score = 0.0

            genre_match = 0
            for genre_id in movie.get("genre_ids", []):
                from tmdb_client import GENRE_MAP

                genre_name = next((k for k, v in GENRE_MAP.items() if v == genre_id), None)
                if genre_name and genre_name in user_genre_counts:
                    genre_match += user_genre_counts[genre_name]

            score += genre_match * 0.4

            if movie.get("rating"):
                rating_diff = abs(movie["rating"] - avg_rating)
                rating_score = max(0, 10 - rating_diff) / 10
                score += rating_score * 0.3

            if movie.get("year"):
                year_diff = abs(movie["year"] - avg_year)
                year_score = max(0, 20 - year_diff) / 20
                score += year_score * 0.2

            if movie.get("popularity"):
                popularity_score = min(movie["popularity"] / 100, 1.0)
                score += popularity_score * 0.1

            scored_movies.append((movie, score))

        scored_movies.sort(key=lambda x: x[1], reverse=True)
        return scored_movies

    def train(self, months_back: int = 6):
        """Train the collaborative filtering model."""
        print("Starting model training...")

        self.load_data(months_back)

        if len(self.recent_movies) < 5:
            print(
                f"Warning: Only {len(self.recent_movies)} recent movies found. Need at least 5 for good recommendations."
            )

        self.extract_features()

        print("\nUser profile summary:")
        print(f"  Top genres: {sorted(self.movie_features['genres'].items(), key=lambda x: x[1], reverse=True)[:5]}")
        print(
            f"  Top directors: {sorted(self.movie_features['directors'].items(), key=lambda x: x[1], reverse=True)[:3]}"
        )
        print(f"  Average rating: {np.mean(self.movie_features['ratings']):.1f}")
        print(f"  Year range: {min(self.movie_features['years'])} - {max(self.movie_features['years'])}")

        self.save_model()
        print(f"\nModel saved to {self.model_path}")

    def predict(self, top_n: int = 5) -> List[Dict]:
        """Generate top N movie recommendations."""
        print("Generating recommendations...")

        candidates = self.get_candidate_movies()

        if not candidates:
            print("No candidate movies found!")
            return []

        scored_movies = self.compute_similarity_scores(candidates)

        recommendations = []
        for movie, score in scored_movies[:top_n]:
            genre_ids = movie.get("genre_ids", [])
            if genre_ids and not isinstance(genre_ids, list):
                genre_ids = list(genre_ids)

            recommendations.append(
                {
                    "title": str(movie["title"]),
                    "year": int(movie["year"]) if movie["year"] else None,
                    "tmdb_id": int(movie["tmdb_id"]),
                    "rating": float(movie.get("rating")) if movie.get("rating") else None,
                    "genres": genre_ids,
                    "overview": str(movie.get("overview", "")),
                    "score": round(float(score), 2),
                    "poster_path": str(movie.get("poster_path")) if movie.get("poster_path") else None,
                }
            )

        return recommendations

    def save_model(self):
        """Save trained model to disk."""
        model_data = {
            "recent_movies": self.recent_movies,
            "movie_features": self.movie_features,
            "trained_date": datetime.now().isoformat(),
        }

        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.model_path, "wb") as f:
            pickle.dump(model_data, f)

    def load_model(self):
        """Load trained model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")

        with open(self.model_path, "rb") as f:
            model_data = pickle.load(f)

        self.recent_movies = model_data["recent_movies"]
        self.movie_features = model_data["movie_features"]

        print(f"Model loaded from {self.model_path}")
        print(f"Trained on: {model_data['trained_date']}")


if __name__ == "__main__":
    model = CollaborativeFilteringModel()
    model.train(months_back=6)

    recommendations = model.predict(top_n=5)

    print("\n" + "=" * 50)
    print("TOP 5 RECOMMENDATIONS")
    print("=" * 50)

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['title']} ({rec['year']})")
        print(f"   Rating: {rec['rating']:.1f}/10")
        print(f"   Match Score: {rec['score']}")
        print(f"   {rec['overview'][:150]}...")
