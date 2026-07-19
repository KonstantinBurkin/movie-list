"""Collaborative filtering using MovieLens dataset."""

import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import polars as pl
import scipy.sparse as sparse
from implicit.cpu.als import AlternatingLeastSquares

# Make `scripts/settings.py` importable whether this module is run standalone
# (`python scripts/recommendation/movielens_cf.py`) or imported as a package.
sys.path.append(str(Path(__file__).resolve().parent.parent))
import settings  # noqa: E402


class MovieLensCF:
    """Collaborative filtering using MovieLens public dataset."""

    def __init__(
        self,
        movielens_path: str = str(settings.MOVIELENS_DATA_DIR),
        model_dir: str = str(settings.MODEL_DIR),
        factors: int = settings.ALS_FACTORS,
        regularization: float = settings.ALS_REGULARIZATION,
        iterations: int = settings.ALS_ITERATIONS,
    ):
        """
        Initialize with MovieLens dataset.

        Args:
            movielens_path: Path to MovieLens dataset director
            model_dir: Directory to cache the trained ALS model
            factors: Number of ALS latent factors
            regularization: ALS regularization strength
            iterations: Number of ALS training iterations
        """
        self.movielens_path = Path(movielens_path)
        self.model_dir = Path(model_dir)
        self.factors = factors
        self.regularization = regularization
        self.iterations = iterations

        self.ratings_df = None
        self.movies_df = None
        self.links_df = None

        self.als_model = None
        self.movie_id_to_idx = None
        self.idx_to_movie_id = None

    def load_movielens_data(self):
        """Load MovieLens dataset."""
        # Check if dataset exists
        if not self.movielens_path.exists():
            raise FileNotFoundError(
                f"MovieLens dataset not found at {self.movielens_path}\n"
                "Run: python scripts/download_movielens.py"
            )

        # Load ratings (userId::movieId::rating::timestamp)
        ratings_path = self.movielens_path / "ratings.dat"
        if ratings_path.exists():
            # ML-1M format
            self.ratings_df = pl.read_csv(
                ratings_path,
                separator="::",
                has_header=False,
                new_columns=["userId", "movieId", "rating", "timestamp"],
            )
        else:
            # ML-latest format
            ratings_csv = self.movielens_path / "ratings.csv"
            self.ratings_df = pl.read_csv(ratings_csv)

        # Load movies
        movies_path = self.movielens_path / "movies.dat"
        if movies_path.exists():
            self.movies_df = pl.read_csv(
                movies_path,
                separator="::",
                has_header=False,
                new_columns=["movieId", "title", "genres"],
            )
        else:
            movies_csv = self.movielens_path / "movies.csv"
            self.movies_df = pl.read_csv(movies_csv)

        # Load IMDB links
        links_path = self.movielens_path / "links.dat"
        if links_path.exists():
            self.links_df = pl.read_csv(
                links_path,
                separator="::",
                has_header=False,
                new_columns=["movieId", "imdbId", "tmdbId"],
            )
        else:
            links_csv = self.movielens_path / "links.csv"
            if links_csv.exists():
                self.links_df = pl.read_csv(links_csv)

        print("Loaded MovieLens dataset:")
        print(f"  - {len(self.ratings_df)} ratings")
        print(f"  - {len(self.movies_df)} movies")
        print(f"  - {self.ratings_df['userId'].n_unique()} users")

    def map_my_movies_to_movielens(
        self, my_movies_df: pl.DataFrame
    ) -> Dict[str, Dict[str, any]]:
        """
        Map user's watched movies to MovieLens movie IDs via IMDB ID.

        Args:
            my_movies_df: User's movie dataframe with 'omdb_id' and 'liked' columns

        Returns:
            Dict mapping omdb_id to {movieId, liked, implicit_rating}
        """
        if self.links_df is None:
            self.load_movielens_data()

        # Convert IMDB IDs (tt1234567 -> 1234567)
        my_imdb_ids = [id.replace("tt", "") for id in my_movies_df["omdb_id"].to_list()]

        # Map to MovieLens IDs with preference weights
        mapping = {}
        for omdb_id, imdb_num, liked in zip(
            my_movies_df["omdb_id"].to_list(),
            my_imdb_ids,
            my_movies_df["liked"].to_list(),
        ):
            # Find in links
            match = self.links_df.filter(pl.col("imdbId") == int(imdb_num))
            if len(match) > 0:
                # Assign implicit ratings:
                # - Liked = 4.5 (strong positive signal)
                # - Watched but not liked = 3.0 (mild positive signal)
                implicit_rating = 4.5 if liked else 3.0
                mapping[omdb_id] = {
                    "movieId": match["movieId"][0],
                    "liked": liked,
                    "implicit_rating": implicit_rating,
                }

        print(f"Mapped {len(mapping)}/{len(my_movies_df)} of your movies to MovieLens")
        liked_count = sum(1 for v in mapping.values() if v["liked"])
        print(f"  - {liked_count} liked (rating ~4.5)")
        print(f"  - {len(mapping) - liked_count} watched (rating ~3.0)")
        return mapping

    def _build_sparse_matrix(self) -> sparse.csr_matrix:
        """Build the user-item confidence matrix (all MovieLens users) for ALS training."""
        user_ids = self.ratings_df["userId"].to_numpy()
        movie_ids = self.ratings_df["movieId"].to_numpy()
        confidence = self.ratings_df["rating"].to_numpy().astype(np.float32)

        unique_users, user_idx = np.unique(user_ids, return_inverse=True)
        unique_movies, movie_idx = np.unique(movie_ids, return_inverse=True)

        self.idx_to_movie_id = unique_movies
        self.movie_id_to_idx = {
            int(movie_id): idx for idx, movie_id in enumerate(unique_movies)
        }

        return sparse.csr_matrix(
            (confidence, (user_idx, movie_idx)),
            shape=(len(unique_users), len(unique_movies)),
        )

    def _get_als_model(self, force_retrain: bool = False) -> AlternatingLeastSquares:
        """Train (or load a cached) ALS model on the full MovieLens ratings matrix."""
        model_path = self.model_dir / "als_model.npz"
        movie_ids_path = self.model_dir / "als_movie_ids.npy"

        if not force_retrain and model_path.exists() and movie_ids_path.exists():
            self.als_model = AlternatingLeastSquares.load(str(model_path))
            self.idx_to_movie_id = np.load(movie_ids_path)
            self.movie_id_to_idx = {
                int(movie_id): idx for idx, movie_id in enumerate(self.idx_to_movie_id)
            }
            print(f"Loaded cached ALS model from {model_path}")
            return self.als_model

        if self.ratings_df is None:
            self.load_movielens_data()

        print("Training ALS model on MovieLens ratings (this may take a while)...")
        user_item_matrix = self._build_sparse_matrix()

        self.als_model = AlternatingLeastSquares(
            factors=self.factors,
            regularization=self.regularization,
            iterations=self.iterations,
            random_state=42,
        )
        self.als_model.fit(user_item_matrix)

        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.als_model.save(str(model_path))
        np.save(movie_ids_path, self.idx_to_movie_id)
        print(f"Cached trained ALS model to {model_path}")

        return self.als_model

    def get_recommendations(
        self,
        my_movies_df: pl.DataFrame,
        top_n: int = 10,
    ) -> List[Dict]:
        """
        Generate recommendations using ALS matrix factorization.

        Args:
            my_movies_df: User's watched movies dataframe with 'omdb_id' and 'liked' columns
            top_n: Number of recommendations

        Returns:
            List of recommended movies with scores
        """
        # Map user's movies to MovieLens with preference weights
        movie_mapping = self.map_my_movies_to_movielens(my_movies_df)

        if not movie_mapping:
            print("Could not map any movies to MovieLens dataset")
            return []

        my_movies_with_ratings = {
            info["movieId"]: info["implicit_rating"] for info in movie_mapping.values()
        }

        self._get_als_model()

        # Fold the user's ratings into the trained item space as a cold-start row vector
        item_idx, confidence = [], []
        for movie_id, rating in my_movies_with_ratings.items():
            idx = self.movie_id_to_idx.get(movie_id)
            if idx is not None:
                item_idx.append(idx)
                confidence.append(rating)

        if not item_idx:
            print("None of your movies are present in the ALS item space")
            return []

        my_user_items = sparse.csr_matrix(
            (confidence, ([0] * len(item_idx), item_idx)),
            shape=(1, len(self.idx_to_movie_id)),
        )

        recommended_idx, scores = self.als_model.recommend(
            userid=0,
            user_items=my_user_items,
            N=top_n,
            filter_already_liked_items=True,
            recalculate_user=True,
        )

        # When fewer valid candidates exist than N, implicit pads the tail with
        # masked placeholder slots (sentinel score = float32 min) instead of
        # shrinking the result - drop those, and belt-and-suspenders exclude
        # anything the user already rated.
        mask_sentinel = np.finfo(np.float32).min
        recommended_movie_ids = []
        kept_scores = []
        for idx, score in zip(recommended_idx, scores):
            if score <= mask_sentinel:
                continue
            movie_id = int(self.idx_to_movie_id[idx])
            if movie_id in my_movies_with_ratings:
                continue
            recommended_movie_ids.append(movie_id)
            kept_scores.append(score)
        scores = kept_scores

        # Pull supplementary stats (avg rating, number of raters) for display only
        stats_by_id = {
            row["movieId"]: row
            for row in (
                self.ratings_df.filter(pl.col("movieId").is_in(recommended_movie_ids))
                .group_by("movieId")
                .agg(
                    [
                        pl.count("userId").alias("num_users"),
                        pl.mean("rating").alias("avg_rating"),
                    ]
                )
                .iter_rows(named=True)
            )
        }

        recs_with_details = pl.DataFrame(
            {
                "movieId": recommended_movie_ids,
                "als_score": [float(s) for s in scores],
            }
        ).join(self.movies_df, on="movieId", how="left")

        results = []
        for row in recs_with_details.iter_rows(named=True):
            # Extract year from title (format: "Movie Title (2020)")
            title = row["title"]
            year = None
            if "(" in title and ")" in title:
                try:
                    year = int(title[title.rfind("(") + 1 : title.rfind(")")])
                    title = title[: title.rfind("(")].strip()
                except ValueError:
                    pass

            movie_stats = stats_by_id.get(row["movieId"], {})

            results.append(
                {
                    "title": title,
                    "year": year,
                    "movielens_id": row["movieId"],
                    "genres": row["genres"],
                    "avg_rating": round(float(movie_stats.get("avg_rating", 0.0)), 2),
                    "num_similar_users": int(movie_stats.get("num_users", 0)),
                    "cf_score": round(float(row["als_score"]), 4),
                }
            )

        return results


if __name__ == "__main__":
    # Example usage
    cf = MovieLensCF()

    # Load user's data (all watched movies, not just liked)
    my_movies = pl.read_parquet(settings.MOVIES_DF_PATH)
    my_movies = my_movies.filter(pl.col("omdb_id") != "Not found")

    print("\nYour movie preferences:")
    liked_count = len(my_movies.filter(pl.col("liked") == True))  # noqa: E712
    total_count = len(my_movies)
    print(f"  Total watched: {total_count}")
    print(f"  Liked: {liked_count}")
    print(f"  Watched (neutral): {total_count - liked_count}")

    # Get recommendations based on both liked AND watched
    recommendations = cf.get_recommendations(my_movies, top_n=10)

    print("\n" + "=" * 60)
    print("COLLABORATIVE FILTERING RECOMMENDATIONS")
    print("=" * 60)

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['title']} ({rec['year']})")
        print(f"   Genres: {rec['genres']}")
        print(f"   Avg Rating: {rec['avg_rating']}/5.0")
        print(f"   Liked by {rec['num_similar_users']} similar users")
        print(f"   CF Score: {rec['cf_score']}")
