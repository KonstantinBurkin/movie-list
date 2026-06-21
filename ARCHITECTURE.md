# Recommendation System Architecture

## System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MOVIE RECOMMENDATION SYSTEM                     │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   Input Data     │
│                  │
│ movies_df.parquet│
│ (671 movies)     │
└────────┬─────────┘
         │
         │ Filter: last 6 months, liked=True
         ▼
┌──────────────────┐
│ Recent Movies    │
│ (Training Data)  │
└────────┬─────────┘
         │
         │ Extract Features
         ▼
┌──────────────────────────────────────────┐
│        Feature Extraction                │
│  • Genre preferences (weighted)          │
│  • Director/Actor patterns               │
│  • Rating distribution                   │
│  • Year preferences                      │
└────────┬─────────────────────────────────┘
         │
         │ Build Profile
         ▼
┌──────────────────────────────────────────┐
│         User Profile                     │
│  Top 3 Genres: [28, 18, 35]             │
│  Avg Rating: 7.8                         │
│  Year Range: 2018-2024                   │
└────────┬─────────────────────────────────┘
         │
         │ Query TMDB API
         ▼
┌──────────────────────────────────────────┐
│      Candidate Generation (TMDB)         │
│                                          │
│  ┌────────────────────────────────┐     │
│  │ Discover by Genre              │     │
│  │ (30 movies)                    │     │
│  └──────────┬─────────────────────┘     │
│             │                            │
│  ┌──────────▼─────────────────────┐     │
│  │ Popular Recent (2020+)         │     │
│  │ (30 movies)                    │     │
│  └──────────┬─────────────────────┘     │
│             │                            │
│  ┌──────────▼─────────────────────┐     │
│  │ Similar to Top-Rated           │     │
│  │ (10 per movie × 10 movies)     │     │
│  └────────────────────────────────┘     │
│                                          │
│  Total: ~150-200 unique candidates       │
└────────┬─────────────────────────────────┘
         │
         │ Compute Similarity
         ▼
┌──────────────────────────────────────────┐
│        Scoring Algorithm                 │
│                                          │
│  For each candidate:                     │
│                                          │
│  Score = Genre Match × 0.4               │
│        + Rating Similarity × 0.3         │
│        + Year Similarity × 0.2           │
│        + Popularity × 0.1                │
│                                          │
│  Sort by Score (descending)              │
└────────┬─────────────────────────────────┘
         │
         │ Select Top 5
         ▼
┌──────────────────────────────────────────┐
│      Top 5 Recommendations               │
│                                          │
│  1. Movie A (2023) - Score: 8.5          │
│  2. Movie B (2022) - Score: 8.2          │
│  3. Movie C (2021) - Score: 7.9          │
│  4. Movie D (2024) - Score: 7.7          │
│  5. Movie E (2023) - Score: 7.5          │
└────────┬─────────────────────────────────┘
         │
         │ Save Output
         ▼
┌──────────────────────────────────────────┐
│            Output Files                  │
│                                          │
│  • recommendations_latest.json           │
│  • recommendations_YYYYMMDD.json         │
│  • recommendations_latest.parquet        │
│  • cf_model.pkl (trained model)          │
└──────────────────────────────────────────┘
```

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application Layer                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │ CLI Interface    │      │ Jupyter Notebook │                │
│  │                  │      │                  │                │
│  │ generate_        │      │ 8_recommendation_│                │
│  │ recommendations  │      │ demo.ipynb       │                │
│  │ .py              │      │                  │                │
│  └────────┬─────────┘      └────────┬─────────┘                │
│           │                         │                           │
│           └──────────┬──────────────┘                           │
│                      │                                          │
└──────────────────────┼──────────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────────┐
│                      │         Model Layer                      │
├──────────────────────┼──────────────────────────────────────────┤
│                      ▼                                          │
│  ┌──────────────────────────────────────────┐                  │
│  │  CollaborativeFilteringModel             │                  │
│  │                                           │                  │
│  │  Methods:                                 │                  │
│  │  • load_data()                            │                  │
│  │  • extract_features()                     │                  │
│  │  • build_genre_profile()                  │                  │
│  │  • get_candidate_movies()                 │                  │
│  │  • compute_similarity_scores()            │                  │
│  │  • train()                                │                  │
│  │  • predict()                              │                  │
│  │  • save_model() / load_model()            │                  │
│  └─────────────┬──────────────┬──────────────┘                  │
│                │              │                                 │
└────────────────┼──────────────┼─────────────────────────────────┘
                 │              │
┌────────────────┼──────────────┼─────────────────────────────────┐
│                │              │      Data Access Layer           │
├────────────────┼──────────────┼─────────────────────────────────┤
│                │              │                                 │
│  ┌─────────────▼────┐   ┌─────▼──────────────┐                 │
│  │  TMDBClient       │   │  Local Data        │                 │
│  │                   │   │                    │                 │
│  │  • search()       │   │  movies_df.parquet │                 │
│  │  • similar()      │   │  cf_model.pkl      │                 │
│  │  • discover()     │   │                    │                 │
│  │  • recommendations│   │                    │                 │
│  └───────────────────┘   └────────────────────┘                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      Automation Layer                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────┐         │
│  │  Claude Code Cron Scheduler                        │         │
│  │  (Job ID: e954a988)                                │         │
│  │                                                     │         │
│  │  Schedule: "17 9 * * 1" (Monday 9:17 AM)           │         │
│  │  Durable: true                                     │         │
│  │  Auto-expires: 7 days                              │         │
│  └────────────────┬───────────────────────────────────┘         │
│                   │                                             │
│                   ▼                                             │
│  ┌────────────────────────────────────────────────────┐         │
│  │  scheduled_retrain.sh                              │         │
│  │                                                     │         │
│  │  • Activates venv                                  │         │
│  │  • Runs generate_recommendations.py                │         │
│  │  • Logs to logs/retrain_*.log                      │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌─────────────┐
│   User's    │
│  Viewing    │
│  History    │
│ (6 months)  │
└──────┬──────┘
       │
       │ movies_df.parquet
       │
       ▼
┌──────────────────────────────────────────────┐
│           Feature Extraction                 │
│                                              │
│  Genres → [Action: 15, Drama: 12, Sci-Fi: 8]│
│  Directors → [Nolan: 3, Villeneuve: 2, ...]  │
│  Avg Rating → 7.8                            │
│  Year Range → 2018-2024                      │
└──────┬───────────────────────────────────────┘
       │
       │ User Profile
       │
       ▼
┌──────────────────────────────────────────────┐
│            TMDB API Queries                  │
│                                              │
│  Query 1: Genre IDs [28, 18, 878]            │
│           ↓                                  │
│           30 movies                          │
│                                              │
│  Query 2: Popular Recent (2020+)             │
│           ↓                                  │
│           30 movies                          │
│                                              │
│  Query 3: Similar to Top 10                  │
│           ↓                                  │
│           10 × 10 = 100 movies               │
│                                              │
│  Deduplicate & Filter Watched                │
│           ↓                                  │
│           ~80-150 unique candidates          │
└──────┬───────────────────────────────────────┘
       │
       │ Candidate List
       │
       ▼
┌──────────────────────────────────────────────┐
│         Similarity Computation               │
│                                              │
│  For each candidate movie:                   │
│    • Compare genres                          │
│    • Compare rating to avg                   │
│    • Compare year to typical                 │
│    • Factor in popularity                    │
│    • Compute weighted score                  │
│                                              │
│  Result: List[(movie, score)]                │
└──────┬───────────────────────────────────────┘
       │
       │ Scored Candidates
       │
       ▼
┌──────────────────────────────────────────────┐
│              Ranking                         │
│                                              │
│  Sort by score (descending)                  │
│  Select top 5                                │
└──────┬───────────────────────────────────────┘
       │
       │ Top 5 Recommendations
       │
       ▼
┌──────────────────────────────────────────────┐
│              Output                          │
│                                              │
│  JSON → recommendations_latest.json          │
│  Parquet → recommendations_latest.parquet    │
│  Model → cf_model.pkl                        │
└──────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data Processing** | Polars | Fast dataframe operations |
| **ML Framework** | scikit-learn | Similarity computation |
| **API Client** | tmdbv3api | TMDB API integration |
| **Serialization** | pickle, JSON | Model & result persistence |
| **Scheduling** | Claude Code Cron | Weekly automation |
| **Scripting** | Python 3.13, Bash | Core logic & automation |
| **Notebooks** | Jupyter | Interactive exploration |

## File Dependencies

```
generate_recommendations.py
    ├── recommendation/collaborative_filtering.py
    │   ├── tmdb_client.py
    │   │   ├── tmdbv3api
    │   │   └── .env (TMDB_API_KEY)
    │   ├── sklearn (similarity)
    │   ├── polars (data processing)
    │   └── pickle (model persistence)
    └── data/movies_df.parquet (input)

Output:
    ├── data/recommendations/*.json
    ├── data/recommendations/*.parquet
    └── models/cf_model.pkl
```

## API Rate Limits

**TMDB API**
- **Rate Limit**: 40 requests per 10 seconds
- **Typical Usage**: ~50-80 requests per training run
- **Estimated Time**: 15-30 seconds per training
- **Status**: Within limits ✓

**Query Breakdown**:
- Genre discovery: 1 request
- Popular recent: 1 request  
- Similar movies: 1 request per reference movie (typically 10)
- Total: ~12-15 requests per run

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Load data | < 0.5s | Polars is fast |
| Feature extraction | < 1s | Simple counting |
| TMDB queries | 15-30s | Network bound |
| Similarity scoring | < 2s | In-memory computation |
| Save results | < 0.5s | JSON + Parquet |
| **Total** | **~20-35s** | End to end |

## Scalability

**Current Capacity**:
- Movies in history: 671 ✓
- Recent movies (6 months): ~50-100 ✓
- Candidates per run: 150-200 ✓
- API calls per run: ~15 ✓

**Bottlenecks**:
1. TMDB API rate limit (not an issue currently)
2. Single-user design (no multi-user CF)

**Future Scaling Options**:
- Cache TMDB results
- Batch processing for multiple users
- Use TMDB's bulk data exports
- Redis for shared candidate cache

---

**Architecture Version**: 1.0  
**Last Updated**: 2026-06-21
