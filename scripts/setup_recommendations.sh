#!/bin/bash
# Setup script for movie recommendation system

set -e

echo "=========================================="
echo "Movie Recommendation System Setup"
echo "=========================================="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "✓ Project directory: $PROJECT_DIR"

if [ ! -f ".env" ]; then
    echo "✗ .env file not found!"
    echo "Creating .env file..."
    cat > .env << 'EOF'
OMDB_API_KEY=your_omdb_key_here
TMDB_API_KEY=your_tmdb_key_here
EOF
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your TMDB API key"
    echo "   Get a free API key at: https://www.themoviedb.org/settings/api"
    echo ""
fi

if [ ! -f "data/movies_df.parquet" ]; then
    echo "✗ No movie data found at data/movies_df.parquet"
    echo "  Please make sure your viewing history is saved there."
    exit 1
fi

echo "✓ Movie data found"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

mkdir -p models data/recommendations logs
touch data/recommendations/.gitkeep models/.gitkeep logs/.gitkeep
echo "✓ Directory structure created"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your TMDB API key"
echo "2. Test the system:"
echo "   python scripts/generate_recommendations.py"
echo ""
echo "3. View recommendations in:"
echo "   data/recommendations/recommendations_latest.json"
echo ""
echo "4. The system will automatically retrain every Monday at 9:17 AM"
echo ""
echo "For more information, see RECOMMENDATION_SYSTEM.md"
echo ""
