#!/usr/bin/env python
"""Verify critical imports for CI/CD."""

import sys
from pathlib import Path

# Add scripts to path
sys.path.append(str(Path(__file__).parent.parent / "scripts"))


def main():
    """Test that all critical imports work."""
    try:
        from tmdb_client import GENRE_MAP, TMDBClient  # noqa: F401
        print("✅ tmdb_client imports successful")

        from recommendation.movielens_cf import MovieLensCF  # noqa: F401
        print("✅ movielens_cf imports successful")

        from generate_recommendations import generate_recommendations  # noqa: F401
        print("✅ generate_recommendations imports successful")

        print("\n✅ All critical imports verified!")
        return 0

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
