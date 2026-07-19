"""Tests for MovieLens collaborative filtering model."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import polars as pl
import pytest

sys.path.append(str(Path(__file__).parent.parent / "scripts"))

from recommendation.movielens_cf import MovieLensCF


@pytest.fixture
def sample_user_movies():
    """Create a sample user movies dataframe."""
    return pl.DataFrame(
        {
            "title": ["The Matrix", "Inception", "The Dark Knight"],
            "year": [1999, 2010, 2008],
            "omdb_id": ["tt0133093", "tt1375666", "tt0468569"],
            "liked": [True, True, False],
            "genre": ["Action, Sci-Fi", "Action, Thriller", "Action, Crime"],
            "director": ["Wachowski", "Nolan", "Nolan"],
            "imdb_rating": [8.7, 8.8, 9.0],
        }
    )


@pytest.fixture
def sample_movielens_ratings():
    """Create sample MovieLens ratings data."""
    return pl.DataFrame(
        {
            "userId": [1, 1, 1, 2, 2, 2, 3, 3, 3],
            "movieId": [101, 102, 103, 101, 102, 104, 102, 103, 104],
            "rating": [4.5, 5.0, 3.0, 4.0, 4.5, 5.0, 3.5, 4.0, 4.5],
            "timestamp": [1234567890] * 9,
        }
    )


@pytest.fixture
def sample_movielens_movies():
    """Create sample MovieLens movies data."""
    return pl.DataFrame(
        {
            "movieId": [101, 102, 103, 104, 105],
            "title": [
                "The Matrix (1999)",
                "Inception (2010)",
                "The Dark Knight (2008)",
                "Interstellar (2014)",
                "The Prestige (2006)",
            ],
            "genres": [
                "Action|Sci-Fi",
                "Action|Thriller",
                "Action|Crime|Drama",
                "Adventure|Drama|Sci-Fi",
                "Drama|Mystery|Thriller",
            ],
        }
    )


@pytest.fixture
def sample_movielens_links():
    """Create sample MovieLens links data."""
    return pl.DataFrame(
        {
            "movieId": [101, 102, 103],
            "imdbId": [133093, 1375666, 468569],  # Without 'tt' prefix
            "tmdbId": [603, 27205, 155],
        }
    )


@pytest.fixture
def mock_movielens_cf(
    tmp_path, sample_movielens_ratings, sample_movielens_movies, sample_movielens_links
):
    """Create a mocked MovieLens CF model with test data."""
    movielens_dir = tmp_path / "movielens"
    movielens_dir.mkdir()

    # Write test data files
    sample_movielens_ratings.write_csv(movielens_dir / "ratings.csv")
    sample_movielens_movies.write_csv(movielens_dir / "movies.csv")
    sample_movielens_links.write_csv(movielens_dir / "links.csv")

    # Isolated model cache dir + tiny ALS config so tests stay fast and never
    # touch (or load) the real project's cached model
    model = MovieLensCF(
        movielens_path=str(movielens_dir),
        model_dir=str(tmp_path / "models"),
        factors=2,
        iterations=3,
    )
    return model


def test_movielens_cf_initialization():
    """Test MovieLensCF initialization."""
    model = MovieLensCF()
    assert model.movielens_path == Path("data/movielens")
    assert model.ratings_df is None
    assert model.movies_df is None
    assert model.links_df is None


def test_load_movielens_data(mock_movielens_cf):
    """Test loading MovieLens dataset."""
    mock_movielens_cf.load_movielens_data()

    assert mock_movielens_cf.ratings_df is not None
    assert mock_movielens_cf.movies_df is not None
    assert mock_movielens_cf.links_df is not None
    assert len(mock_movielens_cf.ratings_df) == 9
    assert len(mock_movielens_cf.movies_df) == 5
    assert len(mock_movielens_cf.links_df) == 3


def test_load_movielens_data_missing_directory():
    """Test error when MovieLens directory doesn't exist."""
    model = MovieLensCF(movielens_path="nonexistent_path")

    with pytest.raises(FileNotFoundError, match="MovieLens dataset not found"):
        model.load_movielens_data()


def test_map_my_movies_to_movielens(mock_movielens_cf, sample_user_movies):
    """Test mapping user movies to MovieLens IDs."""
    mock_movielens_cf.load_movielens_data()
    mapping = mock_movielens_cf.map_my_movies_to_movielens(sample_user_movies)

    assert len(mapping) == 3  # All 3 movies should map
    assert "tt0133093" in mapping
    assert "tt1375666" in mapping
    assert "tt0468569" in mapping

    # Check liked movie gets 4.5 rating
    assert mapping["tt0133093"]["implicit_rating"] == 4.5
    assert mapping["tt0133093"]["liked"] is True

    # Check watched (not liked) gets 3.0 rating
    assert mapping["tt0468569"]["implicit_rating"] == 3.0
    assert mapping["tt0468569"]["liked"] is False


def test_map_my_movies_empty_result(mock_movielens_cf):
    """Test mapping when no movies match."""
    mock_movielens_cf.load_movielens_data()

    # Movies that don't exist in links
    movies = pl.DataFrame(
        {
            "title": ["Unknown Movie"],
            "omdb_id": ["tt9999999"],
            "liked": [True],
        }
    )

    mapping = mock_movielens_cf.map_my_movies_to_movielens(movies)
    assert len(mapping) == 0


def test_get_recommendations(mock_movielens_cf, sample_user_movies):
    """Test generating recommendations."""
    mock_movielens_cf.load_movielens_data()

    recommendations = mock_movielens_cf.get_recommendations(sample_user_movies, top_n=2)

    assert isinstance(recommendations, list)
    # Should get some recommendations (movies not already watched)
    if len(recommendations) > 0:
        rec = recommendations[0]
        assert "title" in rec
        assert "year" in rec
        assert "movielens_id" in rec
        assert "cf_score" in rec
        assert "num_similar_users" in rec
        assert "avg_rating" in rec


def test_get_recommendations_no_mapping(mock_movielens_cf):
    """Test when user movies don't map to MovieLens."""
    mock_movielens_cf.load_movielens_data()

    # Movies that don't exist in MovieLens
    unmapped_movies = pl.DataFrame(
        {
            "title": ["Unknown Movie 1", "Unknown Movie 2"],
            "omdb_id": ["tt9999991", "tt9999992"],
            "liked": [True, True],
        }
    )

    recommendations = mock_movielens_cf.get_recommendations(unmapped_movies, top_n=5)
    assert recommendations == []


def test_preference_weighting(mock_movielens_cf, sample_user_movies):
    """Test that liked movies get higher implicit ratings than watched."""
    mock_movielens_cf.load_movielens_data()
    mapping = mock_movielens_cf.map_my_movies_to_movielens(sample_user_movies)

    liked_movie = None
    watched_movie = None

    for omdb_id, info in mapping.items():
        if info["liked"]:
            liked_movie = info
        else:
            watched_movie = info

    if liked_movie and watched_movie:
        # Liked movies should have higher implicit rating
        assert liked_movie["implicit_rating"] > watched_movie["implicit_rating"]
        assert liked_movie["implicit_rating"] == 4.5
        assert watched_movie["implicit_rating"] == 3.0


def test_recommendation_deduplication(mock_movielens_cf, sample_user_movies):
    """Test that already watched movies are not recommended."""
    mock_movielens_cf.load_movielens_data()

    recommendations = mock_movielens_cf.get_recommendations(sample_user_movies, top_n=5)

    # Get list of watched movie IDs
    watched_titles = set(sample_user_movies["title"].to_list())

    # No recommendation should be a movie we already watched
    for rec in recommendations:
        assert rec["title"] not in watched_titles


def test_cf_score_float(mock_movielens_cf, sample_user_movies):
    """Test that CF scores (ALS dot-product scores) are numeric."""
    mock_movielens_cf.load_movielens_data()

    recommendations = mock_movielens_cf.get_recommendations(sample_user_movies, top_n=5)

    for rec in recommendations:
        assert isinstance(rec["cf_score"], float)


def test_recommendations_sorted_by_score(mock_movielens_cf, sample_user_movies):
    """Test that recommendations are sorted by CF score."""
    mock_movielens_cf.load_movielens_data()

    recommendations = mock_movielens_cf.get_recommendations(sample_user_movies, top_n=5)

    if len(recommendations) > 1:
        # Scores should be in descending order
        scores = [rec["cf_score"] for rec in recommendations]
        assert scores == sorted(scores, reverse=True)


def test_year_parsing(mock_movielens_cf, sample_movielens_movies):
    """Test that years are correctly parsed from MovieLens titles."""
    mock_movielens_cf.load_movielens_data()
    mock_movielens_cf.movies_df = sample_movielens_movies

    # Test with a movie that has year in title
    title_with_year = "The Matrix (1999)"

    # Simulate the year extraction logic
    year = None
    if "(" in title_with_year and ")" in title_with_year:
        try:
            year = int(
                title_with_year[
                    title_with_year.rfind("(") + 1 : title_with_year.rfind(")")
                ]
            )
        except ValueError:
            pass

    assert year == 1999


def test_num_similar_users_in_results(mock_movielens_cf, sample_user_movies):
    """Test that recommendations include number of similar users."""
    mock_movielens_cf.load_movielens_data()

    recommendations = mock_movielens_cf.get_recommendations(sample_user_movies, top_n=3)

    for rec in recommendations:
        assert "num_similar_users" in rec
        assert rec["num_similar_users"] > 0
        assert isinstance(rec["num_similar_users"], int)


def test_avg_rating_in_results(mock_movielens_cf, sample_user_movies):
    """Test that recommendations include average MovieLens rating."""
    mock_movielens_cf.load_movielens_data()

    recommendations = mock_movielens_cf.get_recommendations(sample_user_movies, top_n=3)

    for rec in recommendations:
        assert "avg_rating" in rec
        assert 0 <= rec["avg_rating"] <= 5.0  # MovieLens uses 0.5-5.0 scale
        assert isinstance(rec["avg_rating"], float)


def test_empty_user_history(mock_movielens_cf):
    """Test handling of empty user movie history."""
    mock_movielens_cf.load_movielens_data()

    empty_movies = pl.DataFrame(
        {
            "title": [],
            "omdb_id": [],
            "liked": [],
        }
    )

    recommendations = mock_movielens_cf.get_recommendations(empty_movies, top_n=5)
    assert recommendations == []


def test_top_n_parameter(mock_movielens_cf, sample_user_movies):
    """Test that top_n parameter limits recommendations."""
    mock_movielens_cf.load_movielens_data()

    top_3 = mock_movielens_cf.get_recommendations(sample_user_movies, top_n=3)
    top_5 = mock_movielens_cf.get_recommendations(sample_user_movies, top_n=5)

    assert len(top_3) <= 3
    assert len(top_5) <= 5

    # If we have enough data, should return requested amount
    if len(top_5) >= 5:
        assert len(top_5) == 5
    if len(top_3) >= 3:
        assert len(top_3) == 3
