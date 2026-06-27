"""Main script to train model and generate movie recommendations."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

import json  # noqa: E402
from datetime import datetime  # noqa: E402

import polars as pl  # noqa: E402
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
                    "title": rec["title"],
                    "year": rec["year"],
                    "tmdb_id": tmdb_movie["tmdb_id"],
                    "rating": tmdb_movie.get("rating"),
                    "genres": tmdb_movie.get("genre_ids", []),
                    "overview": tmdb_movie.get("overview", ""),
                    "score": rec["cf_score"],
                    "poster_path": tmdb_movie["poster_path"],
                    "source": "collaborative_filtering",
                    "cf_stats": {
                        "num_similar_users": rec["num_similar_users"],
                        "avg_movielens_rating": rec["avg_rating"],
                    },
                }
            )

    return enriched


def generate_recommendations(top_n: int = 5):
    """
    Generate movie recommendations using collaborative filtering.

    Args:
        top_n: Number of recommendations to generate
    """
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Generating top {top_n} recommendations")
    print("=" * 60 + "\n")

    # Collaborative filtering recommendations
    print("Collaborative filtering recommendations...")
    print("-" * 60)
    try:
        cf_model = MovieLensCF()
        my_movies = pl.read_parquet("data/movies_df.parquet")
        my_movies = my_movies.filter(pl.col("omdb_id") != "Not found")

        # Generate more candidates since we filter for TMDB posters
        cf_recs_raw = cf_model.get_recommendations(my_movies, top_n=top_n * 3)

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

    except FileNotFoundError as e:
        print(f"\n⚠ MovieLens dataset not found: {e}")
        print("  Run: python scripts/download_movielens.py")
        return []
    except Exception as e:
        print(f"\n⚠ CF error: {e}")
        import traceback

        traceback.print_exc()
        return []

    recommendations = recommendations[:top_n]

    if not recommendations:
        print(
            "\nNo recommendations generated. Please check your data and API configuration."
        )
        return []

    output_dir = Path("data/recommendations")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"recommendations_{timestamp}.json"
    latest_path = output_dir / "recommendations_latest.json"

    output_data = {
        "generated_at": datetime.now().isoformat(),
        "recommendations": recommendations,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    df = pl.DataFrame(recommendations)
    parquet_path = output_dir / "recommendations_latest.parquet"
    df.write_parquet(parquet_path)

    print("\n" + "=" * 60)
    print("TOP MOVIE RECOMMENDATIONS")
    print("=" * 60)

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['title']} ({rec['year']})")

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
