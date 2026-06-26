"""Collaborative filtering using MovieLens dataset."""

from pathlib import Path
from typing import Dict, List

import polars as pl


class MovieLensCF:
    """Collaborative filtering using MovieLens public dataset."""

    def __init__(self, movielens_path: str = "data/movielens"):
        """
        Initialize with MovieLens dataset.

        Args:
            movielens_path: Path to MovieLens dataset directory
                Download from: https://files.grouplens.org/datasets/movielens/ml-1m.zip
        """
        self.movielens_path = Path(movielens_path)
        self.ratings_df = None
        self.movies_df = None
        self.links_df = None
        self.user_item_matrix = None

    def load_movielens_data(self):
        """Load MovieLens dataset."""
        # Check if dataset exists
        if not self.movielens_path.exists():
            raise FileNotFoundError(
                f"MovieLens dataset not found at {self.movielens_path}\n"
                "Download from: https://files.grouplens.org/datasets/movielens/ml-1m.zip\n"
                "Or run: python scripts/download_movielens.py"
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

    def find_similar_users(
        self, my_movies_with_ratings: Dict[int, float], top_k: int = 50
    ) -> List[int]:
        """
        Find MovieLens users who have similar taste.

        Args:
            my_movies_with_ratings: Dict of {movieId: implicit_rating}
            top_k: Number of similar users to find

        Returns:
            List of similar user IDs
        """
        if self.ratings_df is None:
            self.load_movielens_data()

        my_movie_ids = list(my_movies_with_ratings.keys())

        # Find users who rated the same movies
        users_who_rated = self.ratings_df.filter(pl.col("movieId").is_in(my_movie_ids))

        # Calculate similarity score for each user
        user_scores = []
        for user_id in users_who_rated["userId"].unique().to_list():
            user_ratings = users_who_rated.filter(pl.col("userId") == user_id)

            # Calculate weighted similarity
            overlap_count = 0
            rating_similarity = 0.0
            preference_match = 0.0

            for row in user_ratings.iter_rows(named=True):
                movie_id = row["movieId"]
                user_rating = row["rating"]
                my_rating = my_movies_with_ratings[movie_id]

                overlap_count += 1

                # Rating similarity (how close are the ratings?)
                rating_diff = abs(user_rating - my_rating)
                rating_similarity += max(0, 5 - rating_diff) / 5.0

                # Preference match (both liked it?)
                if my_rating >= 4.0 and user_rating >= 4.0:
                    preference_match += 2.0  # Both loved it
                elif my_rating >= 3.0 and user_rating >= 3.0:
                    preference_match += 1.0  # Both liked it

            if overlap_count >= max(2, len(my_movie_ids) * 0.2):  # At least 20% overlap
                avg_rating_similarity = rating_similarity / overlap_count
                total_score = (
                    overlap_count * 0.4
                    + avg_rating_similarity * 0.3
                    + preference_match * 0.3
                )
                user_scores.append((user_id, overlap_count, total_score))

        # Sort by total score
        user_scores.sort(key=lambda x: x[2], reverse=True)

        similar_users = [user_id for user_id, _, _ in user_scores[:top_k]]
        print(f"Found {len(similar_users)} similar users")

        if similar_users and len(user_scores) > 0:
            top_user = user_scores[0]
            print(
                f"  Top similar user: ID={top_user[0]}, overlap={top_user[1]} movies, score={top_user[2]:.2f}"
            )

        return similar_users

    def get_recommendations(
        self, my_movies_df: pl.DataFrame, top_n: int = 10
    ) -> List[Dict]:
        """
        Generate recommendations using collaborative filtering.

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

        # Create {movieId: implicit_rating} dict for similarity calculation
        my_movies_with_ratings = {
            info["movieId"]: info["implicit_rating"] for info in movie_mapping.values()
        }

        # Find similar users based on weighted preferences
        similar_users = self.find_similar_users(my_movies_with_ratings, top_k=100)

        if not similar_users:
            print("No similar users found")
            return []

        # Get movies rated by similar users (not already watched by me)
        my_movielens_ids = list(my_movies_with_ratings.keys())
        similar_users_ratings = self.ratings_df.filter(
            (pl.col("userId").is_in(similar_users))
            & (pl.col("rating") >= 3.5)  # Movies they liked (not just watched)
            & (~pl.col("movieId").is_in(my_movielens_ids))  # Not already watched
        )

        # Aggregate recommendations with weighted scoring
        recommendations = (
            similar_users_ratings.group_by("movieId")
            .agg(
                [
                    pl.count("userId").alias("num_users"),
                    pl.mean("rating").alias("avg_rating"),
                    pl.sum("rating").alias("total_rating"),  # Sum for popularity
                ]
            )
            .sort(["total_rating", "num_users"], descending=True)
            .head(top_n * 2)  # Get extra for filtering
        )

        # Join with movie details
        recs_with_details = recommendations.join(
            self.movies_df, on="movieId", how="left"
        )

        # Calculate collaborative filtering score
        # Weight heavily on: how many similar users liked it + their ratings
        recs_with_scores = recs_with_details.with_columns(
            [
                (
                    (
                        pl.col("num_users") / pl.col("num_users").max() * 0.5
                    )  # Popularity among similar users
                    + (pl.col("avg_rating") / 5.0 * 0.3)  # Average rating
                    + (
                        pl.col("total_rating") / pl.col("total_rating").max() * 0.2
                    )  # Total endorsement
                ).alias("cf_score")
            ]
        ).sort("cf_score", descending=True)

        # Convert to list of dicts
        results = []
        for row in recs_with_scores.head(top_n).iter_rows(named=True):
            # Extract year from title (format: "Movie Title (2020)")
            title = row["title"]
            year = None
            if "(" in title and ")" in title:
                try:
                    year = int(title[title.rfind("(") + 1 : title.rfind(")")])
                    title = title[: title.rfind("(")].strip()
                except ValueError:
                    pass

            results.append(
                {
                    "title": title,
                    "year": year,
                    "movielens_id": row["movieId"],
                    "genres": row["genres"],
                    "avg_rating": round(float(row["avg_rating"]), 2),
                    "num_similar_users": int(row["num_users"]),
                    "cf_score": round(float(row["cf_score"]), 2),
                }
            )

        return results


if __name__ == "__main__":
    # Example usage
    cf = MovieLensCF()

    # Load user's data (all watched movies, not just liked)
    my_movies = pl.read_parquet("data/movies_df.parquet")
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
