"""Tests for collaborative filtering recommendation generation script."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent / "scripts"))

from generate_recommendations import enrich_cf_recommendations_with_tmdb, generate_recommendations


@pytest.fixture
def mock_cf_recommendations():
    """Sample CF recommendations output."""
    return [
        {
            'title': 'Test Movie 1',
            'year': 2023,
            'movielens_id': 123,
            'genres': 'Action, Drama',
            'avg_rating': 4.2,
            'num_similar_users': 45,
            'cf_score': 0.85
        },
        {
            'title': 'Test Movie 2',
            'year': 2024,
            'movielens_id': 456,
            'genres': 'Comedy',
            'avg_rating': 4.0,
            'num_similar_users': 38,
            'cf_score': 0.78
        }
    ]


@pytest.fixture
def mock_enriched_recommendations():
    """Sample enriched recommendations with TMDB data."""
    return [
        {
            'title': 'Test Movie 1',
            'year': 2023,
            'tmdb_id': 789,
            'rating': 8.4,
            'genres': [28, 18],
            'overview': 'A test movie',
            'score': 0.85,
            'poster_path': '/test1.jpg',
            'source': 'collaborative_filtering',
            'cf_stats': {
                'num_similar_users': 45,
                'avg_movielens_rating': 4.2
            }
        },
        {
            'title': 'Test Movie 2',
            'year': 2024,
            'tmdb_id': 101,
            'rating': 8.0,
            'genres': [35],
            'overview': 'Another test',
            'score': 0.78,
            'poster_path': '/test2.jpg',
            'source': 'collaborative_filtering',
            'cf_stats': {
                'num_similar_users': 38,
                'avg_movielens_rating': 4.0
            }
        }
    ]


def test_generate_recommendations_with_cf(tmp_path, mock_cf_recommendations, mock_enriched_recommendations):
    """Test generating recommendations with collaborative filtering."""
    with patch('generate_recommendations.MovieLensCF') as MockCF, \
         patch('generate_recommendations.pl'), \
         patch('generate_recommendations.TMDBClient'), \
         patch('generate_recommendations.enrich_cf_recommendations_with_tmdb') as mock_enrich:

        mock_cf_model = MockCF.return_value
        mock_cf_model.get_recommendations.return_value = mock_cf_recommendations
        mock_enrich.return_value = mock_enriched_recommendations

        with patch('generate_recommendations.Path') as MockPath:
            mock_output_dir = tmp_path / 'recommendations'
            mock_output_dir.mkdir(parents=True, exist_ok=True)
            MockPath.return_value = mock_output_dir

            result = generate_recommendations(top_n=2)

            assert len(result) == 2
            mock_cf_model.get_recommendations.assert_called_once()


def test_generate_recommendations_empty_result(tmp_path):
    """Test handling when MovieLens returns no recommendations."""
    with patch('generate_recommendations.MovieLensCF') as MockCF, \
         patch('generate_recommendations.pl'):

        mock_cf_model = MockCF.return_value
        mock_cf_model.get_recommendations.return_value = []

        result = generate_recommendations(top_n=5)

        assert result == []


def test_generate_recommendations_movielens_not_found():
    """Test handling when MovieLens dataset is not found."""
    with patch('generate_recommendations.MovieLensCF') as MockCF, \
         patch('generate_recommendations.pl'):

        MockCF.side_effect = FileNotFoundError("MovieLens dataset not found")

        result = generate_recommendations(top_n=5)

        assert result == []


def test_enrich_cf_recommendations_with_tmdb_success(mock_cf_recommendations):
    """Test enriching CF recommendations with TMDB data successfully."""
    mock_tmdb_client = Mock()
    mock_tmdb_client.get_movie_by_title.side_effect = [
        {
            'tmdb_id': 789,
            'rating': 8.4,
            'genre_ids': [28, 18],
            'overview': 'A test movie about action',
            'poster_path': '/test1.jpg'
        },
        {
            'tmdb_id': 101,
            'rating': 8.0,
            'genre_ids': [35],
            'overview': 'A comedy test movie',
            'poster_path': '/test2.jpg'
        }
    ]

    enriched = enrich_cf_recommendations_with_tmdb(mock_cf_recommendations, mock_tmdb_client)

    assert len(enriched) == 2
    # Check first recommendation
    assert enriched[0]['title'] == 'Test Movie 1'
    assert enriched[0]['tmdb_id'] == 789
    assert enriched[0]['rating'] == 8.4
    assert enriched[0]['overview'] == 'A test movie about action'
    assert enriched[0]['poster_path'] == '/test1.jpg'
    assert enriched[0]['source'] == 'collaborative_filtering'
    assert enriched[0]['cf_stats']['num_similar_users'] == 45


def test_enrich_cf_recommendations_tmdb_not_found(mock_cf_recommendations):
    """Test enriching when TMDB doesn't find the movie - should skip these movies."""
    mock_tmdb_client = Mock()
    mock_tmdb_client.get_movie_by_title.return_value = None

    enriched = enrich_cf_recommendations_with_tmdb(mock_cf_recommendations, mock_tmdb_client)

    # Movies without TMDB data should be skipped
    assert len(enriched) == 0


def test_enrich_cf_recommendations_no_tmdb_id(mock_cf_recommendations):
    """Test enriching when TMDB returns data without tmdb_id - should skip these movies."""
    mock_tmdb_client = Mock()
    mock_tmdb_client.get_movie_by_title.return_value = {
        'rating': 8.4,
        'genre_ids': [28],
        'overview': 'Test',
        'poster_path': '/test.jpg'
        # Missing tmdb_id
    }

    enriched = enrich_cf_recommendations_with_tmdb(mock_cf_recommendations, mock_tmdb_client)

    # Movies without tmdb_id should be skipped
    assert len(enriched) == 0


def test_enrich_cf_recommendations_tmdb_exception(mock_cf_recommendations):
    """Test handling TMDB exceptions gracefully - should skip movies with errors."""
    mock_tmdb_client = Mock()
    mock_tmdb_client.get_movie_by_title.side_effect = Exception("TMDB API error")

    enriched = enrich_cf_recommendations_with_tmdb(mock_cf_recommendations, mock_tmdb_client)

    # Movies with TMDB errors should be skipped
    assert len(enriched) == 0


def test_enrich_cf_recommendations_partial_tmdb_data(mock_cf_recommendations):
    """Test handling partial TMDB data (some movies found, some not) - only includes movies with posters."""
    mock_tmdb_client = Mock()
    mock_tmdb_client.get_movie_by_title.side_effect = [
        {
            'tmdb_id': 789,
            'rating': 8.4,
            'genre_ids': [28, 18],
            'overview': 'A test movie',
            'poster_path': '/test1.jpg'
        },
        None  # Second movie not found
    ]

    enriched = enrich_cf_recommendations_with_tmdb(mock_cf_recommendations, mock_tmdb_client)

    # Only movies with TMDB data and posters should be included
    assert len(enriched) == 1
    assert enriched[0]['tmdb_id'] == 789
    assert enriched[0]['rating'] == 8.4
    assert enriched[0]['poster_path'] == '/test1.jpg'


def test_enrich_cf_recommendations_preserves_cf_stats(mock_cf_recommendations):
    """Test that CF stats are preserved in enriched recommendations."""
    mock_tmdb_client = Mock()
    mock_tmdb_client.get_movie_by_title.return_value = {
        'tmdb_id': 789,
        'rating': 8.4,
        'genre_ids': [28],
        'overview': 'Test',
        'poster_path': '/test.jpg'
    }

    enriched = enrich_cf_recommendations_with_tmdb(mock_cf_recommendations, mock_tmdb_client)

    # Check CF stats are preserved
    assert enriched[0]['cf_stats']['num_similar_users'] == 45
    assert enriched[0]['cf_stats']['avg_movielens_rating'] == 4.2
    assert enriched[1]['cf_stats']['num_similar_users'] == 38
    assert enriched[1]['cf_stats']['avg_movielens_rating'] == 4.0


def test_enrich_cf_recommendations_empty_list():
    """Test enriching empty recommendations list."""
    mock_tmdb_client = Mock()
    enriched = enrich_cf_recommendations_with_tmdb([], mock_tmdb_client)
    assert enriched == []


def test_enrich_cf_recommendations_missing_poster(mock_cf_recommendations):
    """Test handling TMDB response with missing poster - should skip these movies."""
    mock_tmdb_client = Mock()
    mock_tmdb_client.get_movie_by_title.return_value = {
        'tmdb_id': 789,
        'rating': 8.4,
        'genre_ids': [28],
        'overview': 'Test movie',
        'poster_path': None  # No poster - should skip
    }

    enriched = enrich_cf_recommendations_with_tmdb(mock_cf_recommendations, mock_tmdb_client)

    # Movies without poster_path should be skipped
    assert len(enriched) == 0


def test_enrich_cf_recommendations_with_all_optional_fields(mock_cf_recommendations):
    """Test handling TMDB response with all fields including optional ones."""
    mock_tmdb_client = Mock()
    mock_tmdb_client.get_movie_by_title.return_value = {
        'tmdb_id': 789,
        'rating': 8.4,
        'genre_ids': [28, 18],
        'overview': 'A comprehensive test movie',
        'poster_path': '/test.jpg'
    }

    enriched = enrich_cf_recommendations_with_tmdb(mock_cf_recommendations, mock_tmdb_client)

    assert len(enriched) == 2
    assert enriched[0]['tmdb_id'] == 789
    assert enriched[0]['rating'] == 8.4
    assert enriched[0]['genres'] == [28, 18]
    assert enriched[0]['overview'] == 'A comprehensive test movie'
    assert enriched[0]['poster_path'] == '/test.jpg'
