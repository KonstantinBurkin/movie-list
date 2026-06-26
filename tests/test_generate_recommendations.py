"""Tests for collaborative filtering recommendation generation script."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.append(str(Path(__file__).parent.parent / "scripts"))

from generate_recommendations import generate_recommendations


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
