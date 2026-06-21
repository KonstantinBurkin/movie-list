# Movie Recommendation System

A collaborative filtering-based recommendation system that predicts movies you'll enjoy based on your viewing history.

## Overview

This system analyzes your watched movies from the last 6 months and uses collaborative filtering to recommend 5 new films you might like. The model automatically retrains every week to incorporate new viewing data.

## Features

- **Collaborative Filtering**: Item-based recommendation using genre, director, actor preferences, and ratings
- **TMDB Integration**: Accesses The Movie Database API to discover new movies similar to your preferences
- **Automatic Retraining**: Weekly scheduled retraining to keep recommendations fresh
- **Preference Learning**: Learns from:
  - Genres you prefer
  - Directors and actors you enjoy
  - Rating patterns
  - Release year preferences
  - Popularity trends

## Setup

### 1. Get TMDB API Key

1. Create a free account at [The Movie Database](https://www.themoviedb.org/)
2. Go to Settings → API
3. Request an API key (v3 auth)
4. Add it to `.env`:

```bash
TMDB_API_KEY=your_api_key_here
```

### 2. Install Dependencies

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Generate Recommendations

Run the recommendation system manually:

```bash
python scripts/generate_recommendations.py
```

Options:
- `--no-retrain`: Use existing model without retraining
- `--top-n N`: Generate N recommendations (default: 5)
- `--months-back N`: Use N months of history (default: 6)

Example:
```bash
python scripts/generate_recommendations.py --top-n 10 --months-back 12
```

### View Recommendations

Latest recommendations are saved in:
- `data/recommendations/recommendations_latest.json`
- `data/recommendations/recommendations_latest.parquet`

### Scheduled Retraining

The system automatically retrains every **Monday at 9:17 AM** via Claude Code's scheduler.

To check scheduled tasks:
```bash
# View in Claude Code
/cron-list
```

Logs are saved in:
- `logs/retrain_YYYYMMDD_HHMMSS.log`
- `logs/retrain_latest.log` (symlink to most recent)

### Manual Retraining

Run the retraining script manually:

```bash
./scripts/scheduled_retrain.sh
```

## How It Works

### 1. Data Collection
- Loads movies you watched in the last 6 months
- Filters for movies you liked (liked=True)
- Extracts preference features (genres, directors, actors, ratings)

### 2. Candidate Generation
- Discovers movies from TMDB based on:
  - Your top 3 preferred genres
  - Popular recent releases (2020+)
  - Movies similar to your highest-rated films

### 3. Scoring & Ranking
- Computes similarity scores for each candidate:
  - **Genre match** (40%): Alignment with your preferred genres
  - **Rating similarity** (30%): Rating close to your average
  - **Year preference** (20%): Recent releases similar to your viewing patterns
  - **Popularity** (10%): Currently trending films

### 4. Recommendation Output
- Top 5 movies with highest similarity scores
- Includes title, year, rating, overview, and poster

## File Structure

```
movie-list/
├── scripts/
│   ├── tmdb_client.py              # TMDB API client
│   ├── recommendation/
│   │   ├── __init__.py
│   │   └── collaborative_filtering.py  # Core CF model
│   ├── generate_recommendations.py  # Main recommendation script
│   └── scheduled_retrain.sh        # Weekly retrain script
├── models/
│   └── cf_model.pkl                # Trained model
├── data/
│   ├── movies_df.parquet           # Your viewing history
│   └── recommendations/
│       ├── recommendations_latest.json
│       └── recommendations_YYYYMMDD_HHMMSS.json
└── logs/
    └── retrain_YYYYMMDD_HHMMSS.log
```

## Troubleshooting

### No recommendations generated

**Issue**: Empty recommendations list

**Solutions**:
1. Check TMDB API key is set in `.env`
2. Ensure you have at least 5 movies watched in the last 6 months
3. Verify internet connection for TMDB API calls
4. Check logs in `logs/` directory

### API rate limiting

**Issue**: TMDB API returns 429 errors

**Solution**: TMDB allows 40 requests per 10 seconds. The system is designed to stay within limits, but if you hit rate limits, wait a few minutes and retry.

### Model not loading

**Issue**: FileNotFoundError for `cf_model.pkl`

**Solution**: Run with retraining: `python scripts/generate_recommendations.py`

## Future Enhancements

- [ ] Add user-based collaborative filtering with multiple users
- [ ] Integrate additional data sources (IMDB, Rotten Tomatoes)
- [ ] Add content-based filtering for cold-start problem
- [ ] Create web interface to display recommendations
- [ ] Add feedback loop to improve recommendations
- [ ] Support for TV shows and series

## Weekly Retraining Schedule

- **Frequency**: Every Monday at 9:17 AM (local time)
- **Duration**: ~2-3 minutes depending on viewing history size
- **Auto-expires**: After 7 days, will fire one final time then stop (restart with new cron job)
- **Durable**: Survives Claude Code restarts

---

**Last Updated**: 2026-06-21
