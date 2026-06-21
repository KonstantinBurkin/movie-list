"""Main script to train model and generate movie recommendations."""

import sys
from pathlib import Path
from datetime import datetime
import json
import polars as pl

sys.path.append(str(Path(__file__).parent))

from recommendation.collaborative_filtering import CollaborativeFilteringModel


def generate_recommendations(retrain: bool = True, top_n: int = 5, months_back: int = 6):
    """
    Generate movie recommendations.

    Args:
        retrain: Whether to retrain the model before generating recommendations
        top_n: Number of recommendations to generate
        months_back: Number of months of viewing history to use
    """
    print("=" * 60)
    print("MOVIE RECOMMENDATION SYSTEM")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Generating top {top_n} recommendations")
    print(f"Using {months_back} months of viewing history")
    print("=" * 60 + "\n")

    model = CollaborativeFilteringModel()

    if retrain:
        print("Training model...\n")
        model.train(months_back=months_back)
    else:
        print("Loading existing model...\n")
        try:
            model.load_model()
        except FileNotFoundError:
            print("No existing model found. Training new model...\n")
            model.train(months_back=months_back)

    recommendations = model.predict(top_n=top_n)

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
        print(f"\n{i}. {rec['title']} ({rec['year']})")
        print(f"   TMDB ID: {rec['tmdb_id']}")
        print(f"   Rating: {rec['rating']:.1f}/10" if rec["rating"] else "   Rating: N/A")
        print(f"   Match Score: {rec['score']}")
        print(f"   Overview: {rec['overview'][:200]}...")
        if rec.get("poster_path"):
            print(f"   Poster: https://image.tmdb.org/t/p/w500{rec['poster_path']}")

    print("\n" + "=" * 60)
    print(f"Recommendations saved to:")
    print(f"  - {json_path}")
    print(f"  - {latest_path}")
    print(f"  - {parquet_path}")
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

    args = parser.parse_args()

    try:
        generate_recommendations(retrain=not args.no_retrain, top_n=args.top_n, months_back=args.months_back)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
