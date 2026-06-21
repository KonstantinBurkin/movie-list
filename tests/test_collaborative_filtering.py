"""Tests for collaborative filtering model."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import polars as pl
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent / "scripts"))

from recommendation.collaborative_filtering import CollaborativeFilteringModel


@pytest.fixture
def sample_movies_df():
    """Create a sample movies dataframe."""
    today = datetime.now().date()
    return pl.DataFrame({
        'index': [1, 2, 3, 4, 5],
        'title': ['Movie A', 'Movie B', 'Movie C', 'Movie D', 'Movie E'],
        'year': [2020, 2021, 2022, 2023, 2024],
        'viewed': [
            today - timedelta(days=30),
            today - timedelta(days=60),
            today - timedelta(days=90),
            today - timedelta(days=120),
            today - timedelta(days=300)  # Too old
        ],
        'liked': [True, True, True, True, True],
        'omdb_id': ['tt1', 'tt2', 'tt3', 'tt4', 'tt5'],
        'genre': ['Action, Drama', 'Comedy', 'Drama, Thriller', 'Action', 'Horror'],
        'director': ['Director A', 'Director B', 'Director A', 'Director C', 'Director D'],
        'country': ['USA', 'USA', 'UK', 'USA', 'France'],
        'actors': ['Actor 1, Actor 2', 'Actor 3', 'Actor 1, Actor 4', 'Actor 5', 'Actor 6'],
        'box_office': [100, 200, 150, 300, 50],
        'writer': ['Writer A', 'Writer B', 'Writer C', 'Writer A', 'Writer D'],
        'language': ['English', 'English', 'English', 'English', 'French'],
        'imdb_rating': [8.0, 7.5, 8.5, 7.0, 6.5],
        'comment': ['', '', '', '', '']
    })


@pytest.fixture
def mock_model(tmp_path, sample_movies_df):
    """Create a mocked collaborative filtering model."""
    data_path = tmp_path / "movies_df.parquet"
    sample_movies_df.write_parquet(data_path)

    with patch('recommendation.collaborative_filtering.TMDBClient'):
        model = CollaborativeFilteringModel(data_path=str(data_path))
        model.model_path = tmp_path / "cf_model.pkl"
        return model


def test_model_initialization(mock_model):
    """Test model initialization."""
    assert mock_model.data_path is not None
    assert mock_model.movies_df is None
    assert mock_model.recent_movies is None


def test_load_data(mock_model):
    """Test loading and filtering movie data."""
    recent = mock_model.load_data(months_back=6)

    assert recent is not None
    assert len(recent) == 4  # 4 movies within 6 months
    assert all(recent['liked'])


def test_extract_features(mock_model):
    """Test feature extraction from movies."""
    mock_model.load_data(months_back=6)
    features = mock_model.extract_features()

    assert 'genres' in features
    assert 'directors' in features
    assert 'actors' in features
    assert 'years' in features
    assert 'ratings' in features

    assert 'Action' in features['genres']
    assert 'Drama' in features['genres']
    assert len(features['years']) == 4
    assert len(features['ratings']) == 4


def test_build_genre_profile(mock_model):
    """Test building genre preference profile."""
    mock_model.load_data(months_back=6)
    mock_model.extract_features()

    genre_ids = mock_model.build_genre_profile()

    assert isinstance(genre_ids, list)
    assert len(genre_ids) <= 3
    assert all(isinstance(gid, int) for gid in genre_ids)


def test_compute_similarity_scores(mock_model):
    """Test similarity score computation."""
    mock_model.load_data(months_back=6)
    mock_model.extract_features()

    candidates = [
        {
            'tmdb_id': 1,
            'title': 'Test Movie 1',
            'year': 2023,
            'genre_ids': [28, 18],  # Action, Drama
            'rating': 8.0,
            'popularity': 50.0
        },
        {
            'tmdb_id': 2,
            'title': 'Test Movie 2',
            'year': 2024,
            'genre_ids': [35],  # Comedy
            'rating': 6.0,
            'popularity': 30.0
        }
    ]

    scored = mock_model.compute_similarity_scores(candidates)

    assert len(scored) == 2
    assert all(isinstance(score, float) for _, score in scored)
    # First movie should score higher (matches Action/Drama preferences)
    assert scored[0][1] >= scored[1][1]


def test_save_and_load_model(mock_model):
    """Test model persistence."""
    mock_model.load_data(months_back=6)
    mock_model.extract_features()
    mock_model.save_model()

    assert mock_model.model_path.exists()

    # Create new model and load saved data
    with patch('recommendation.collaborative_filtering.TMDBClient'):
        new_model = CollaborativeFilteringModel()
        new_model.model_path = mock_model.model_path
        new_model.load_model()

        assert new_model.recent_movies is not None
        assert new_model.movie_features is not None
        assert len(new_model.recent_movies) == len(mock_model.recent_movies)


def test_train(mock_model):
    """Test model training."""
    mock_model.train(months_back=6)

    assert mock_model.recent_movies is not None
    assert mock_model.movie_features is not None
    assert mock_model.model_path.exists()


def test_predict_with_mock_candidates(mock_model):
    """Test prediction with mocked TMDB responses."""
    mock_model.load_data(months_back=6)
    mock_model.extract_features()

    mock_candidates = [
        {
            'tmdb_id': i,
            'title': f'Recommended Movie {i}',
            'year': 2023,
            'genre_ids': [28, 18],
            'rating': 8.0,
            'popularity': 50.0,
            'overview': 'A great movie...',
            'poster_path': f'/poster{i}.jpg'
        }
        for i in range(1, 11)
    ]

    with patch.object(mock_model, 'get_candidate_movies', return_value=mock_candidates):
        recommendations = mock_model.predict(top_n=5)

        assert len(recommendations) == 5
        for rec in recommendations:
            assert 'title' in rec
            assert 'year' in rec
            assert 'tmdb_id' in rec
            assert 'rating' in rec
            assert 'score' in rec
            assert isinstance(rec['score'], (int, float))


def test_insufficient_data_warning(mock_model, sample_movies_df, tmp_path):
    """Test warning when insufficient recent data."""
    # Create dataframe with only old movies
    old_df = sample_movies_df.with_columns(
        pl.lit(datetime.now().date() - timedelta(days=365)).alias('viewed')
    )
    data_path = tmp_path / "old_movies.parquet"
    old_df.write_parquet(data_path)

    with patch('recommendation.collaborative_filtering.TMDBClient'):
        model = CollaborativeFilteringModel(data_path=str(data_path))
        recent = model.load_data(months_back=6)

        assert len(recent) == 0


def test_genre_counting(mock_model):
    """Test genre preference counting."""
    mock_model.load_data(months_back=6)
    features = mock_model.extract_features()

    # Action appears in 2 movies, Drama in 2 movies
    assert features['genres']['Action'] == 2
    assert features['genres']['Drama'] == 2
    assert features['genres']['Comedy'] == 1


def test_director_counting(mock_model):
    """Test director preference counting."""
    mock_model.load_data(months_back=6)
    features = mock_model.extract_features()

    # Director A appears in 2 movies
    assert features['directors']['Director A'] == 2
    assert features['directors']['Director B'] == 1
