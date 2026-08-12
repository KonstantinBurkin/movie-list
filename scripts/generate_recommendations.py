"""Main script to train model and generate movie recommendations."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

import json  # noqa: E402
from datetime import datetime  # noqa: E402

import polars as pl  # noqa: E402
import settings  # noqa: E402
from recommendation.movielens_cf import MovieLensCF  # noqa: E402
from tmdb_client import TMDBClient  # noqa: E402


def enrich_cf_recommendations_with_tmdb(cf_recs: list, tmdb_client: TMDBClient) -> list:
    """
    Enrich MovieLens CF recommendations with TMDB data.

    Args:
        cf_recs: List of CF recommendations from MovieLens
        tmdb_client: TMDB client for fetching movie details (required)

    Returns:
        List of enriched recommendations with TMDB data (movies without TMDB data are skipped)
    """
    enriched = []

    for rec in cf_recs:
        # Try to find movie on TMDB
        tmdb_movie = None
        try:
            tmdb_movie = tmdb_client.get_movie_by_title(rec["title"], rec.get("year"))
        except Exception:
            # TMDB lookup failed, skip this recommendation
            continue

        # Only add recommendations that have TMDB data with poster
        if tmdb_movie and tmdb_movie.get("tmdb_id") and tmdb_movie.get("poster_path"):
            enriched.append(
                {
                    "title": str(rec["title"]),
                    "year": int(rec["year"]) if rec["year"] else None,
                    "tmdb_id": int(tmdb_movie["tmdb_id"]),
                    "rating": (
                        float(tmdb_movie["rating"])
                        if tmdb_movie.get("rating")
                        else None
                    ),
                    "genres": list(tmdb_movie.get("genre_ids", [])),
                    "overview": str(tmdb_movie.get("overview", "")),
                    "score": float(rec["cf_score"]),
                    "poster_path": str(tmdb_movie["poster_path"]),
                    "source": "collaborative_filtering",
                    "belongs_to_collection": tmdb_client.is_part_of_collection(
                        tmdb_movie["tmdb_id"]
                    ),
                    "cf_stats": {
                        "num_similar_users": int(rec["num_similar_users"]),
                        "avg_movielens_rating": float(rec["avg_rating"]),
                    },
                }
            )

    return enriched


def load_recommended_history() -> dict:
    """Load the log of previously recommended movies, keyed by str(tmdb_id)."""
    history_path = settings.RECOMMENDATIONS_DIR / "recommended_history.json"
    if not history_path.exists():
        return {}
    with open(history_path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_recommended_history(recs: list) -> None:
    """Record newly served recommendations in the history log."""
    history_path = settings.RECOMMENDATIONS_DIR / "recommended_history.json"
    history = load_recommended_history()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for rec in recs:
        key = str(rec["tmdb_id"])
        history[key] = {
            "title": rec["title"],
            "year": rec["year"],
            "first_recommended_at": history.get(key, {}).get(
                "first_recommended_at", timestamp
            ),
        }

    settings.RECOMMENDATIONS_DIR.mkdir(parents=True, exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def filter_recs(recs: list, top_n: int, history: dict | None = None) -> list:
    # remove sequels/franchise entries
    recs = [rec for rec in recs if not rec.get("belongs_to_collection")]

    # remove movies already served in a previous run
    if history:
        recs = [rec for rec in recs if str(rec["tmdb_id"]) not in history]

    recs = recs[:top_n]
    return recs


def save_recommendations(recs: list) -> None:
    output_dir = settings.RECOMMENDATIONS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"recommendations_{timestamp}.json"
    latest_path = output_dir / "recommendations_latest.json"

    output_data = {
        "generated_at": timestamp,
        "recommendations": recs,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


def generate_recommendations(top_n: int = 5):
    """
    Generate movie recommendations using collaborative filtering.

    Args:
        top_n: Number of recommendations to generate
    """

    print("Collaborative filtering recommendations...")
    print("-" * 60)
    try:
        cf_model = MovieLensCF()
        my_movies = pl.read_parquet(settings.MOVIES_DF_PATH)
        my_movies = my_movies.filter(pl.col("omdb_id") != "Not found")

        # Generate more candidates since we filter for TMDB posters
        cf_recs_raw = cf_model.get_recommendations(my_movies, top_n=top_n * 10)

        if cf_recs_raw:
            # Enrich with TMDB data (required - only movies with posters are included)
            tmdb_client = TMDBClient()
            recommendations = enrich_cf_recommendations_with_tmdb(
                cf_recs_raw, tmdb_client
            )
            print(
                f"\n✓ Generated {len(recommendations)} CF recommendations with TMDB posters"
            )
        else:
            print("\n⚠ No CF recommendations generated")
            return []

    except Exception as e:
        print(f"Generate recs error: {e}")
        import traceback

        traceback.print_exc()
        return []

    history = load_recommended_history()
    recommendations = filter_recs(recommendations, top_n, history)

    if not recommendations:
        print(
            "\nNo recommendations generated. Please check your data and API configuration."
        )
        return []

    save_recommendations(recommendations)
    update_recommended_history(recommendations)

    return recommendations


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate movie recommendations")
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of recommendations to generate (default: 5)",
    )

    args = parser.parse_args()

    try:
        generate_recommendations(top_n=args.top_n)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
