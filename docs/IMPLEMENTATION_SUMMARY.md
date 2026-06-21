# Movie Recommendation System - Implementation Summary

## Overview

Successfully implemented a collaborative filtering recommendation system that:
- ✅ Analyzes viewing history from the last 6 months
- ✅ Uses TMDB API to discover new movies
- ✅ Generates 5 personalized recommendations
- ✅ Automatically retrains weekly (every Monday at 9:17 AM)
- ✅ Saves recommendations in JSON and Parquet formats

## What Was Built

### 1. Core Components

#### TMDB Integration (`scripts/tmdb_client.py`)
- Client for The Movie Database API
- Functions to search movies, get similar movies, discover by genre
- Genre mapping for recommendation matching
- **Requires**: TMDB API key (free from themoviedb.org)

#### Collaborative Filtering Model (`scripts/recommendation/collaborative_filtering.py`)
- Item-based collaborative filtering using cosine similarity
- Feature extraction from viewing history:
  - Genre preferences (weighted by ratings)
  - Director and actor preferences
  - Rating patterns
  - Year preferences
- Scoring algorithm:
  - Genre match: 40%
  - Rating similarity: 30%
  - Year preference: 20%
  - Popularity: 10%
- Model persistence with pickle

#### Recommendation Generator (`scripts/generate_recommendations.py`)
- CLI tool to train and generate recommendations
- Options for retraining, number of recommendations, history window
- Saves output in multiple formats
- Logging and error handling

### 2. Automation

#### Weekly Retraining
- **Schedule**: Every Monday at 9:17 AM (local time)
- **Script**: `scripts/scheduled_retrain.sh`
- **Managed by**: Claude Code's CronCreate (durable, survives restarts)
- **Logs**: Saved to `logs/retrain_YYYYMMDD_HHMMSS.log`
- **Auto-expires**: After 7 days (restart with new cron job if needed)

### 3. Data Management

#### Input
- `data/movies_df.parquet` - Your viewing history
  - Filters for `liked=True` and `viewed` in last 6 months
  - Minimum 5 movies recommended for good results

#### Output
- `data/recommendations/recommendations_latest.json` - Latest recommendations
- `data/recommendations/recommendations_YYYYMMDD_HHMMSS.json` - Timestamped versions
- `data/recommendations/recommendations_latest.parquet` - For data analysis
- `models/cf_model.pkl` - Trained model (for fast predictions without retraining)

### 4. Tools & Scripts

| File | Purpose |
|------|---------|
| `scripts/setup_recommendations.sh` | One-time setup script |
| `scripts/generate_recommendations.py` | Main CLI for recommendations |
| `scripts/scheduled_retrain.sh` | Weekly retraining automation |
| `notebooks/8_recommendation_demo.ipynb` | Interactive demo notebook |

### 5. Documentation

- `RECOMMENDATION_SYSTEM.md` - Full system documentation
- `README.md` - Updated with recommendation features
- `IMPLEMENTATION_SUMMARY.md` - This file

## How It Works

### Training Phase
1. Load movies watched in last 6 months where `liked=True`
2. Extract user preference features:
   - Count genres, directors, actors
   - Calculate average rating and year
3. Save model to `models/cf_model.pkl`

### Prediction Phase
1. Load trained model (or retrain if needed)
2. Build genre profile from top preferences
3. Fetch candidate movies from TMDB:
   - Movies matching preferred genres (min rating 7.0)
   - Popular recent releases (2020+)
   - Movies similar to highly-rated films
4. Score each candidate using similarity algorithm
5. Return top 5 highest-scoring movies
6. Save recommendations to JSON and Parquet

### Scoring Algorithm

For each candidate movie, compute:

```python
score = (genre_match × 0.4) + 
        (rating_similarity × 0.3) + 
        (year_similarity × 0.2) + 
        (popularity × 0.1)
```

Where:
- **genre_match**: Number of matching genres weighted by your viewing frequency
- **rating_similarity**: How close the movie's rating is to your average
- **year_similarity**: How close the release year is to your typical viewing
- **popularity**: Current TMDB popularity score (normalized)

## Dependencies Added

```txt
scikit-learn==1.6.1
scipy==1.15.2
scikit-surprise==1.1.4
tmdbv3api==1.9.0
```

## Quick Start

1. **Get TMDB API Key**
   ```bash
   # Sign up at https://www.themoviedb.org/
   # Go to Settings → API → Request API Key
   # Add to .env:
   echo "TMDB_API_KEY=your_key_here" >> .env
   ```

2. **Run Setup**
   ```bash
   ./scripts/setup_recommendations.sh
   ```

3. **Generate Recommendations**
   ```bash
   python scripts/generate_recommendations.py
   ```

4. **View Results**
   ```bash
   cat data/recommendations/recommendations_latest.json
   ```

## Weekly Schedule Details

- **Job ID**: e954a988
- **Schedule**: `17 9 * * 1` (Monday at 9:17 AM local time)
- **Persisted**: Yes (survives Claude Code restarts)
- **Location**: `.claude/scheduled_tasks.json`
- **Auto-expires**: After 7 days

To check status:
```
In Claude Code: /cron-list
```

## Monitoring

### Logs
- Retraining logs: `logs/retrain_*.log`
- Latest log: `logs/retrain_latest.log` (symlink)

### Recommendations History
All generated recommendations are timestamped and saved, allowing you to:
- Track how recommendations change over time
- Compare predictions before/after retraining
- Analyze recommendation quality

## Future Enhancements

Potential improvements:
1. **User-based CF**: Multi-user collaborative filtering
2. **Content-based filtering**: For cold-start problem
3. **Hybrid approach**: Combine CF with content features
4. **Feedback loop**: Learn from which recommendations you actually watch
5. **Web interface**: Display recommendations in Streamlit dashboard
6. **TV shows**: Extend to series recommendations
7. **More data sources**: IMDB, Rotten Tomatoes integration
8. **Ensemble models**: Combine multiple algorithms

## Technical Notes

### Why Item-Based CF?
- Works well with single-user scenario
- Leverages TMDB's extensive movie database
- No cold-start problem (uses content features)
- Fast predictions after training

### Why TMDB?
- Free API with generous rate limits (40 req/10s)
- Comprehensive movie database (600K+ movies)
- Good similarity/recommendation endpoints
- Active community and updates

### Scheduling Approach
- Uses Claude Code's native cron functionality
- Durable (persists across sessions)
- Runs at off-peak time (9:17 AM) to avoid :00/:30 API congestion
- Auto-expires after 7 days as safety measure

## Files Created

```
movie-list/
├── scripts/
│   ├── tmdb_client.py                      # TMDB API client
│   ├── recommendation/
│   │   ├── __init__.py
│   │   └── collaborative_filtering.py      # Core model
│   ├── generate_recommendations.py         # Main CLI
│   ├── scheduled_retrain.sh                # Weekly cron script
│   └── setup_recommendations.sh            # One-time setup
├── notebooks/
│   └── 8_recommendation_demo.ipynb         # Interactive demo
├── models/
│   ├── .gitkeep
│   └── cf_model.pkl                        # (generated)
├── data/recommendations/
│   ├── .gitkeep
│   ├── recommendations_latest.json         # (generated)
│   └── recommendations_*.json              # (generated)
├── logs/
│   ├── .gitkeep
│   └── retrain_*.log                       # (generated)
├── .claude/
│   └── scheduled_tasks.json                # (generated)
├── RECOMMENDATION_SYSTEM.md                # User documentation
├── IMPLEMENTATION_SUMMARY.md               # This file
├── .gitignore                              # Updated
├── README.md                               # Updated
└── requirements.txt                        # Updated
```

## Testing

To test the system:

```bash
# Manual test
python scripts/generate_recommendations.py --top-n 5 --months-back 6

# Test without retraining (faster)
python scripts/generate_recommendations.py --no-retrain

# Test with more recommendations
python scripts/generate_recommendations.py --top-n 10

# Test scheduled script
./scripts/scheduled_retrain.sh
```

## Troubleshooting

### "No recommendations generated"
- Check TMDB API key is set in `.env`
- Ensure at least 5 liked movies in last 6 months
- Verify internet connection

### "Model not found"
- Run with retraining: `python scripts/generate_recommendations.py`
- Model auto-trains on first run

### Rate limiting
- TMDB allows 40 requests per 10 seconds
- System stays within limits, but wait if hit

### Cron not firing
- Check scheduled tasks: In Claude Code, use `/cron-list`
- Verify `.claude/scheduled_tasks.json` exists
- Remember: auto-expires after 7 days

---

**Implementation Date**: 2026-06-21  
**Model Type**: Item-based Collaborative Filtering  
**Data Source**: TMDB API  
**Scheduling**: Claude Code Cron
