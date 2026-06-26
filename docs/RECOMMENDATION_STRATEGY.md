# Movie Recommendation Strategy

## Your Preference Model

You've defined a simple but effective preference model:

- **Watched** = Interesting (implicit rating: **3.0/5.0**)
  - "I watched it, so it had some appeal"
  - Positive signal, but mild

- **Liked** = Very Interesting (implicit rating: **4.5/5.0**)
  - "I watched AND liked it"
  - Strong positive signal

This approach is used in collaborative filtering to find "users like you."

## How Collaborative Filtering Works

### 1. Map Your Movies
```
Your Movie              → MovieLens ID  → Implicit Rating
─────────────────────────────────────────────────────────
The Dark Knight (liked) → ml_id: 12345  → 4.5
Inception (watched)     → ml_id: 67890  → 3.0
```

### 2. Find Similar Users
```python
MovieLens users who:
- Watched the same movies as you
- Rated them similarly:
  - If you liked it (4.5) → they rated it 4.0-5.0
  - If you watched it (3.0) → they rated it 3.0-4.0
- High overlap = more similar
```

### 3. Get Recommendations
```
Similar users also liked:
- Movie A: 45 similar users, avg rating 4.2 → Score: 0.85
- Movie B: 30 similar users, avg rating 4.5 → Score: 0.78
- Movie C: 60 similar users, avg rating 3.8 → Score: 0.72
```

## Scoring Algorithm

The collaborative filtering score combines:

```python
CF Score = 
  + 0.5 × (num_similar_users / max_users)     # How many liked it
  + 0.3 × (avg_rating / 5.0)                   # How much they liked it
  + 0.2 × (total_rating / max_total_rating)   # Total endorsement
```

**Why this works:**
- Prioritizes movies that MANY similar users liked
- Balances popularity with quality (high ratings)
- Accounts for total endorsement (30 users at 4.5 > 10 users at 5.0)

## User Similarity Scoring

When finding similar users:

```python
Similarity Score = 
  + 0.4 × overlap_count              # How many shared movies
  + 0.3 × rating_similarity          # How close are ratings
  + 0.3 × preference_match           # Did you both love/like same movies

Preference Match Bonus:
- Both loved it (≥4.0) → +2.0 points
- Both liked it (≥3.0) → +1.0 point
```

**Example:**
```
User A vs You:
- Overlap: 25 movies
- Rating similarity: 0.85 (very close)
- Preference match: 18 (both loved 9 movies)
→ Total Score: 25×0.4 + 0.85×0.3 + 18×0.3 = 15.65
```

## Watched vs Liked Impact

### Scenario 1: You watched 100 movies, liked 80
```python
Your profile:
- 80 movies rated 4.5 (strong signal)
- 20 movies rated 3.0 (mild signal)

Similar users will be:
- Those who LOVED the same 80 movies you did
- And also watched (but maybe didn't love) the 20 neutral ones
```

### Scenario 2: You watched 100 movies, liked 20
```python
Your profile:
- 20 movies rated 4.5 (very selective)
- 80 movies rated 3.0 (many neutral)

Similar users will be:
- Picky users who also LOVED those specific 20
- Recommendations will be more niche/refined
```

## Implementation

### Current Structure

```
scripts/recommendation/
├── collaborative_filtering.py  # Content-based (your current)
└── movielens_cf.py            # Collaborative filtering (NEW)
```

### How to Use

**Step 1: Download MovieLens**
```bash
python scripts/download_movielens.py
# Downloads to: data/movielens/
```

**Step 2: Test Collaborative Filtering**
```bash
python scripts/recommendation/movielens_cf.py
```

**Output:**
```
Your movie preferences:
  Total watched: 671
  Liked: 450
  Watched (neutral): 221

Mapped 580/671 of your movies to MovieLens
  - 390 liked (rating ~4.5)
  - 190 watched (rating ~3.0)

Found 85 similar users
  Top similar user: ID=3421, overlap=42 movies, score=28.34

COLLABORATIVE FILTERING RECOMMENDATIONS
═══════════════════════════════════════

1. The Shawshank Redemption (1994)
   Genres: Drama, Crime
   Avg Rating: 4.5/5.0
   Liked by 62 similar users
   CF Score: 0.92
```

**Step 3: Integrate into Your System**

Update `scripts/generate_recommendations.py`:

```python
from recommendation.collaborative_filtering import CollaborativeFilteringModel
from recommendation.movielens_cf import MovieLensCF

def generate_recommendations(retrain=True, top_n=5, months_back=6):
    # Content-based (current system)
    content_model = CollaborativeFilteringModel()
    content_model.train(months_back=months_back)
    content_recs = content_model.predict(top_n=10)
    
    # Collaborative filtering (MovieLens)
    try:
        cf_model = MovieLensCF()
        my_movies = pl.read_parquet("data/movies_df.parquet")
        cf_recs = cf_model.get_recommendations(my_movies, top_n=10)
    except FileNotFoundError:
        print("MovieLens dataset not found - using content-based only")
        cf_recs = []
    
    # Blend recommendations
    final_recs = blend_recommendations(content_recs, cf_recs, top_n=top_n)
    
    return final_recs

def blend_recommendations(content_recs, cf_recs, top_n=5):
    """Blend content-based and collaborative filtering recommendations."""
    # Simple blending: alternate between sources
    blended = []
    seen_titles = set()
    
    # Interleave: CF, content, CF, content...
    for i in range(max(len(content_recs), len(cf_recs))):
        # Add CF rec
        if i < len(cf_recs):
            rec = cf_recs[i]
            if rec['title'] not in seen_titles:
                blended.append({**rec, 'source': 'collaborative'})
                seen_titles.add(rec['title'])
        
        # Add content rec
        if i < len(content_recs):
            rec = content_recs[i]
            if rec['title'] not in seen_titles:
                blended.append({**rec, 'source': 'content'})
                seen_titles.add(rec['title'])
        
        if len(blended) >= top_n:
            break
    
    return blended[:top_n]
```

## Advantages of This Approach

✅ **True collaborative filtering** - finds real users with similar taste  
✅ **Respects your preference intensity** - liked movies weighted higher  
✅ **No database needed** - uses public MovieLens dataset  
✅ **Transparent scoring** - you can see why recommendations appear  
✅ **Hybrid-ready** - can combine with content-based system  
✅ **Privacy-friendly** - your data stays local  

## Limitations

❌ **MovieLens data is from 2019** - no movies after that  
❌ **Mapping rate ~70-80%** - some movies don't match IMDB IDs  
❌ **Cold start** - needs at least 10-20 mapped movies to work well  

## Tips for Better Recommendations

1. **Mark more movies as liked** - gives stronger signal
2. **Watch diverse genres** - helps find more similar users
3. **Use hybrid approach** - blend CF + content-based
4. **Update MovieLens annually** - download latest dataset
5. **Set rating thresholds carefully** - lower threshold = more recs

## Future Improvements

### Phase 1: Basic CF (Current)
- [x] MovieLens integration
- [x] IMDB ID mapping
- [x] Similar user finding
- [x] Weighted preferences (liked > watched)

### Phase 2: Hybrid System
- [ ] Blend CF + content-based
- [ ] Diversity in recommendations
- [ ] Explain why each movie recommended

### Phase 3: Advanced CF
- [ ] Matrix factorization (SVD)
- [ ] Neural collaborative filtering
- [ ] Context-aware recommendations (mood, time of day)

### Phase 4: Multi-User (Optional)
- [ ] Add real user profiles
- [ ] SQLite for ratings storage
- [ ] User-to-user recommendations
- [ ] Social features (share lists, compare taste)

## Conclusion

Your preference model is:
- **Simple**: Watched = interesting, Liked = very interesting
- **Effective**: Translates naturally to rating scale (3.0 vs 4.5)
- **Scalable**: Works with collaborative filtering algorithms

The MovieLens integration gives you collaborative filtering without building a multi-user system!
