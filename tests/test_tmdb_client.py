"""Tests for TMDB client."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent / "scripts"))

from tmdb_client import GENRE_MAP, TMDBClient


class MockMovie:
    """Mock TMDB movie object."""

    def __init__(self, id, title, release_date, vote_average, popularity, overview, poster_path, genre_ids):
        self.id = id
        self.title = title
        self.release_date = release_date
        self.vote_average = vote_average
        self.popularity = popularity
        self.overview = overview
        self.poster_path = poster_path
        self.genre_ids = genre_ids


@pytest.fixture
def mock_tmdb_client():
    """Create a mocked TMDB client."""
    with patch('tmdb_client.TMDb'), \
         patch('tmdb_client.Movie'), \
         patch('tmdb_client.Discover'):
        client = TMDBClient()
        return client


@pytest.fixture
def sample_movie():
    """Create a sample movie object."""
    return MockMovie(
        id=550,
        title="Fight Club",
        release_date="1999-10-15",
        vote_average=8.4,
        popularity=82.5,
        overview="A ticking-time-bomb insomniac...",
        poster_path="/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        genre_ids=[18, 53]
    )


def test_genre_map_completeness():
    """Test that GENRE_MAP contains expected genres."""
    expected_genres = ['Action', 'Drama', 'Comedy', 'Thriller', 'Horror']
    for genre in expected_genres:
        assert genre in GENRE_MAP
        assert isinstance(GENRE_MAP[genre], int)


def test_format_movie_details(mock_tmdb_client, sample_movie):
    """Test movie detail formatting."""
    result = mock_tmdb_client._format_movie_details(sample_movie)

    assert result['tmdb_id'] == 550
    assert result['title'] == "Fight Club"
    assert result['year'] == 1999
    assert result['rating'] == 8.4
    assert result['popularity'] == 82.5
    assert 'overview' in result
    assert result['genre_ids'] == [18, 53]


def test_format_movie_details_missing_fields(mock_tmdb_client):
    """Test formatting with missing fields."""
    minimal_movie = Mock(id=123, title="Test Movie")
    minimal_movie.release_date = None
    minimal_movie.vote_average = None
    minimal_movie.genre_ids = []
    minimal_movie.overview = None
    minimal_movie.poster_path = None
    minimal_movie.popularity = None

    result = mock_tmdb_client._format_movie_details(minimal_movie)

    assert result['tmdb_id'] == 123
    assert result['title'] == "Test Movie"
    assert result['year'] is None
    assert result['rating'] is None


def test_get_movie_by_title(mock_tmdb_client, sample_movie):
    """Test searching for a movie by title."""
    mock_tmdb_client.movie.search = Mock(return_value=[sample_movie])

    result = mock_tmdb_client.get_movie_by_title("Fight Club", 1999)

    assert result is not None
    assert result['title'] == "Fight Club"
    assert result['year'] == 1999


def test_get_movie_by_title_not_found(mock_tmdb_client):
    """Test searching for non-existent movie."""
    mock_tmdb_client.movie.search = Mock(return_value=[])

    result = mock_tmdb_client.get_movie_by_title("NonExistentMovie")

    assert result is None


def test_get_similar_movies(mock_tmdb_client, sample_movie):
    """Test getting similar movies."""
    mock_tmdb_client.movie.similar = Mock(return_value=[sample_movie, sample_movie])

    results = mock_tmdb_client.get_similar_movies(550, limit=2)

    assert len(results) == 2
    assert all(r['tmdb_id'] == 550 for r in results)


def test_discover_by_genres(mock_tmdb_client, sample_movie):
    """Test discovering movies by genre."""
    mock_tmdb_client.discover.discover_movies = Mock(return_value=[sample_movie])

    results = mock_tmdb_client.discover_by_genres([18, 28], min_rating=7.0, limit=10)

    assert len(results) >= 0
    mock_tmdb_client.discover.discover_movies.assert_called_once()


def test_discover_popular_recent(mock_tmdb_client, sample_movie):
    """Test discovering popular recent movies."""
    mock_tmdb_client.discover.discover_movies = Mock(return_value=[sample_movie])

    results = mock_tmdb_client.discover_popular_recent(min_year=2020, limit=10)

    assert len(results) >= 0
    mock_tmdb_client.discover.discover_movies.assert_called_once()


def test_client_initialization():
    """Test TMDB client initialization."""
    with patch('tmdb_client.os.getenv') as mock_getenv:
        mock_getenv.return_value = 'test_api_key'
        with patch('tmdb_client.TMDb'), \
             patch('tmdb_client.Movie'), \
             patch('tmdb_client.Discover'):
            client = TMDBClient()
            assert client.tmdb.api_key == 'test_api_key'
            assert client.tmdb.language == 'en'
