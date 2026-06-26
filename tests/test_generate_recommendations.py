"""Tests for recommendation generation script."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.append(str(Path(__file__).parent.parent / "scripts"))

from generate_recommendations import generate_recommendations


@pytest.fixture
def mock_recommendations():
    """Sample recommendations output."""
    return [
        {
            'title': 'Test Movie 1',
            'year': 2023,
            'tmdb_id': 123,
            'rating': 8.0,
            'genres': [28, 18],
            'overview': 'A test movie',
            'score': 8.5,
            'poster_path': '/test1.jpg'
        },
        {
            'title': 'Test Movie 2',
            'year': 2024,
            'tmdb_id': 456,
            'rating': 7.5,
            'genres': [35],
            'overview': 'Another test',
            'score': 7.8,
            'poster_path': '/test2.jpg'
        }
    ]


def test_generate_recommendations_with_retraining(tmp_path, mock_recommendations):
    """Test generating recommendations with model retraining."""
    with patch('generate_recommendations.ContentBasedModel') as MockModel:
        mock_model = MockModel.return_value
        mock_model.predict.return_value = mock_recommendations

        # Mock the output directory
        with patch('generate_recommendations.Path') as MockPath:
            mock_output_dir = tmp_path / 'recommendations'
            mock_output_dir.mkdir(parents=True, exist_ok=True)
            MockPath.return_value = mock_output_dir

            result = generate_recommendations(retrain=True, top_n=5, months_back=6)

            assert len(result) == 2
            mock_model.train.assert_called_once_with(months_back=6)
            mock_model.predict.assert_called_once_with(top_n=5)


def test_generate_recommendations_without_retraining(tmp_path, mock_recommendations):
    """Test generating recommendations without retraining."""
    with patch('generate_recommendations.ContentBasedModel') as MockModel:
        mock_model = MockModel.return_value
        mock_model.predict.return_value = mock_recommendations

        with patch('generate_recommendations.Path') as MockPath:
            mock_output_dir = tmp_path / 'recommendations'
            mock_output_dir.mkdir(parents=True, exist_ok=True)
            MockPath.return_value = mock_output_dir

            result = generate_recommendations(retrain=False, top_n=5, months_back=6)

            assert len(result) == 2
            mock_model.load_model.assert_called_once()
            mock_model.predict.assert_called_once_with(top_n=5)


def test_generate_recommendations_empty_result(tmp_path):
    """Test handling of empty recommendations."""
    with patch('generate_recommendations.ContentBasedModel') as MockModel:
        mock_model = MockModel.return_value
        mock_model.predict.return_value = []

        with patch('generate_recommendations.Path') as MockPath:
            mock_output_dir = tmp_path / 'recommendations'
            mock_output_dir.mkdir(parents=True, exist_ok=True)
            MockPath.return_value = mock_output_dir

            result = generate_recommendations(retrain=True, top_n=5, months_back=6)

            assert result == []


def test_output_file_creation(tmp_path, mock_recommendations):
    """Test that output files are created correctly."""
    output_dir = tmp_path / 'recommendations'
    output_dir.mkdir(parents=True, exist_ok=True)

    with patch('generate_recommendations.ContentBasedModel') as MockModel:
        mock_model = MockModel.return_value
        mock_model.predict.return_value = mock_recommendations

        # Override Path to use tmp_path
        original_path = Path

        def mock_path_factory(*args):
            if args and 'data/recommendations' in str(args[0]):
                return output_dir
            return original_path(*args)

        with patch('generate_recommendations.Path', side_effect=mock_path_factory):
            result = generate_recommendations(retrain=True, top_n=2, months_back=6)

            # Check files were created
            assert any(output_dir.glob('recommendations_*.json'))
            assert len(result) == 2
