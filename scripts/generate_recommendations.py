"""Main script to train model and generate movie recommendations."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

import json  # noqa: E402
from datetime import datetime  # noqa: E402

import polars as pl  # noqa: E402
from recommendation.content_based import ContentBasedModel  # noqa: E402
from recommendation.movielens_cf import MovieLensCF  # noqa: E402
from tmdb_client import TMDBClient  # noqa: E402


def enrich_cf_recommendations_with_tmdb(cf_recs: list, tmdb_client: TMDBClient) -> list:
    """
    Enrich MovieLens CF recommendations with TMDB data.

    Args:
        cf_recs: List of CF recommendations from MovieLens
        tmdb_client: TMDB client for fetching movie details

    Returns:
        List of enriched recommendations with TMDB data
    """
    enriched = []

    for rec in cf_recs:
        # Try to find movie on TMDB
        tmdb_movie = tmdb_client.get_movie_by_title(rec["title"], rec.get("year"))

        if tmdb_movie and tmdb_movie.get("tmdb_id"):
            enriched.append(
                {
                    "title": rec["title"],
                    "year": rec["year"],
                    "tmdb_id": tmdb_movie["tmdb_id"],
                    "rating": tmdb_movie.get("rating"),
                    "genres": tmdb_movie.get("genre_ids", []),
                    "overview": tmdb_movie.get("overview", ""),
                    "score": rec["cf_score"],
                    "poster_path": tmdb_movie.get("poster_path"),
                    "source": "collaborative_filtering",
                    "cf_stats": {
                        "num_similar_users": rec["num_similar_users"],
                        "avg_movielens_rating": rec["avg_rating"],
                    },
                }
            )
        else:
            # Fallback: use MovieLens data without TMDB enrichment
            enriched.append(
                {
                    "title": rec["title"],
                    "year": rec["year"],
                    "tmdb_id": None,
                    "rating": rec["avg_rating"] * 2,  # Convert 5-scale to 10-scale
                    "genres": [],
                    "overview": f"Recommended by {rec['num_similar_users']} similar users (MovieLens)",
                    "score": rec["cf_score"],
                    "poster_path": None,
                    "source": "collaborative_filtering",
                    "cf_stats": {
                        "num_similar_users": rec["num_similar_users"],
                        "avg_movielens_rating": rec["avg_rating"],
                    },
                }
            )

    return enriched


def blend_recommendations(content_recs: list, cf_recs: list, top_n: int = 5) -> list:
    """
    Blend content-based and collaborative filtering recommendations.

    Args:
        content_recs: Content-based recommendations
        cf_recs: Collaborative filtering recommendations
        top_n: Number of final recommendations

    Returns:
        Blended list of recommendations
    """
    blended = []
    seen_titles = set()

    # Interleave recommendations (CF first as it's often more personalized)
    cf_idx = 0
    content_idx = 0

    while len(blended) < top_n and (cf_idx < len(cf_recs) or content_idx < len(content_recs)):
        # Add CF recommendation
        if cf_idx < len(cf_recs):
            rec = cf_recs[cf_idx]
            if rec["title"] not in seen_titles:
                blended.append(rec)
                seen_titles.add(rec["title"])
            cf_idx += 1

        if len(blended) >= top_n:
            break

        # Add content recommendation
        if content_idx < len(content_recs):
            rec = content_recs[content_idx]
            # Add source tag if not present
            if "source" not in rec:
                rec = {**rec, "source": "content_based"}
            if rec["title"] not in seen_titles:
                blended.append(rec)
                seen_titles.add(rec["title"])
            content_idx += 1

    return blended[:top_n]


def generate_recommendations(
    retrain: bool = True, top_n: int = 5, months_back: int = 6, use_cf: bool = True
):
    """
    Generate movie recommendations using hybrid approach.

    Args:
        retrain: Whether to retrain the model before generating recommendations
        top_n: Number of recommendations to generate
        months_back: Number of months of viewing history to use
        use_cf: Whether to use collaborative filtering (requires MovieLens dataset)
    """
    print("=" * 60)
    print("MOVIE RECOMMENDATION SYSTEM (HYBRID)")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Generating top {top_n} recommendations")
    print(f"Using {months_back} months of viewing history")
    print(f"Collaborative Filtering: {'Enabled' if use_cf else 'Disabled'}")
    print("=" * 60 + "\n")

    # Content-based recommendations
    print("[1/2] Content-based recommendations...")
    print("-" * 60)
    content_model = ContentBasedModel()

    if retrain:
        print("Training content-based model...\n")
        content_model.train(months_back=months_back)
    else:
        print("Loading existing content-based model...\n")
        try:
            content_model.load_model()
        except FileNotFoundError:
            print("No existing model found. Training new model...\n")
            content_model.train(months_back=months_back)

    content_recommendations = content_model.predict(top_n=top_n * 2)

    # Collaborative filtering recommendations
    cf_recommendations = []
    if use_cf:
        print("\n[2/2] Collaborative filtering recommendations...")
        print("-" * 60)
        try:
            cf_model = MovieLensCF()
            my_movies = pl.read_parquet("data/movies_df.parquet")
            my_movies = my_movies.filter(pl.col("omdb_id") != "Not found")

            cf_recs_raw = cf_model.get_recommendations(my_movies, top_n=top_n * 2)

            if cf_recs_raw:
                # Enrich with TMDB data
                tmdb_client = TMDBClient()
                cf_recommendations = enrich_cf_recommendations_with_tmdb(cf_recs_raw, tmdb_client)
                print(f"\n✓ Generated {len(cf_recommendations)} CF recommendations")
            else:
                print("\n⚠ No CF recommendations generated")

        except FileNotFoundError as e:
            print(f"\n⚠ MovieLens dataset not found: {e}")
            print("  Run: python scripts/download_movielens.py")
            print("  Falling back to content-based only")
        except Exception as e:
            print(f"\n⚠ CF error: {e}")
            print("  Falling back to content-based only")

    # Blend recommendations
    if cf_recommendations:
        print("\n" + "-" * 60)
        print("Blending recommendations...")
        recommendations = blend_recommendations(content_recommendations, cf_recommendations, top_n=top_n)
    else:
        recommendations = content_recommendations[:top_n]

    if not recommendations:
        print("\nNo recommendations generated. Please check your data and API configuration.")
        return []

    output_dir = Path("data/recommendations")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"recommendations_{timestamp}.json"
    latest_path = output_dir / "recommendations_latest.json"

    output_data = {
        "generated_at": datetime.now().isoformat(),
        "months_back": months_back,
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
        source_label = "🤝 CF" if rec.get("source") == "collaborative_filtering" else "📊 Content"
        print(f"\n{i}. [{source_label}] {rec['title']} ({rec['year']})")
        print(f"   TMDB ID: {rec.get('tmdb_id', 'N/A')}")
        print(f"   Rating: {rec['rating']:.1f}/10" if rec.get("rating") else "   Rating: N/A")
        print(f"   Match Score: {rec['score']:.2f}")

        if rec.get("cf_stats"):
            print(f"   CF: {rec['cf_stats']['num_similar_users']} similar users liked this")

        print(f"   Overview: {rec['overview'][:200]}..." if rec.get("overview") else "   Overview: N/A")
        if rec.get("poster_path"):
            print(f"   Poster: https://image.tmdb.org/t/p/w500{rec['poster_path']}")

    print("\n" + "=" * 60)
    print("Recommendations saved to:")
    print(f"  - {json_path}")
    print(f"  - {latest_path}")
    print(f"  - {parquet_path}")
    print("=" * 60)

    # Print breakdown
    cf_count = sum(1 for r in recommendations if r.get("source") == "collaborative_filtering")
    content_count = len(recommendations) - cf_count
    print("\nRecommendation sources:")
    print(f"  - Collaborative Filtering: {cf_count}")
    print(f"  - Content-based: {content_count}")
    print("=" * 60)

    return recommendations


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate movie recommendations")
    parser.add_argument("--no-retrain", action="store_true", help="Use existing model without retraining")
    parser.add_argument("--top-n", type=int, default=5, help="Number of recommendations to generate (default: 5)")
    parser.add_argument(
        "--months-back", type=int, default=6, help="Number of months of viewing history to use (default: 6)"
    )
    parser.add_argument(
        "--no-cf",
        action="store_true",
        help="Disable collaborative filtering (content-based only)",
    )

    args = parser.parse_args()

    try:
        generate_recommendations(
            retrain=not args.no_retrain,
            top_n=args.top_n,
            months_back=args.months_back,
            use_cf=not args.no_cf,
        )
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
