# Collaborative Filtering for Movie Recommendations

## Current System
Your current recommendation system is **content-based filtering** - it only uses YOUR viewing history to find similar movies based on:
- Genres you like
- Directors/actors you watch
- Rating patterns
- Year preferences

## True Collaborative Filtering Options

### Option 1: Use Public Datasets (Recommended) ⭐

Integrate public movie rating datasets to find "users like you":

#### **1A. MovieLens Dataset** (Best option)
```python
# Free dataset with millions of ratings
# URL: https://grouplens.org/datasets/movielens/

Datasets available:
- MovieLens 100K: 100,000 ratings from 600 users on 9,000 movies
- MovieLens 1M: 1 million ratings from 6,000 users on 4,000 movies  
- MovieLens 25M: 25 million ratings from 162,000 users on 62,000 movies

Format:
- userId, movieId, rating, timestamp
- Movie metadata (title, genres, year)
- Already mapped to IMDB IDs!
```

**How it works:**
1. Download MovieLens dataset
2. Map your watched movies to MovieLens movie IDs (via IMDB ID)
3. Find users in the dataset who rated your movies similarly
4. Recommend movies those similar users liked

**Pros:**
- ✅ Free, high-quality data
- ✅ Already cleaned and structured
- ✅ IMDB ID mapping included
- ✅ No need to collect your own users
- ✅ Millions of ratings available

**Cons:**
- ❌ Dataset is from 2019 (no recent movies)
- ❌ Need to update periodically

#### **1B. TMDB Community Ratings**
```python
# Already using TMDB API
# Can get vote_average and vote_count

Example:
{
  "title": "The Dark Knight",
  "vote_average": 8.5,
  "vote_count": 32000  # 32k users rated it
}
```

**How it works:**
- Use TMDB's aggregated ratings as "implicit users"
- Find movies with similar rating patterns
- Weight by vote_count (more votes = more reliable)

**Pros:**
- ✅ Already integrated (using TMDB API)
- ✅ Up-to-date ratings
- ✅ No extra data needed

**Cons:**
- ❌ Less personalized (aggregated data only)
- ❌ No individual user profiles

---

### Option 2: Build Multi-User System

If you want REAL users watching movies together:

#### **2A. Add User Profiles to Your App**

```python
# New data structure
users_df.parquet:
  - user_id (primary key)
  - username
  - email
  - created_at

user_movies_df.parquet:
  - user_id (foreign key)
  - movie_id (foreign key)
  - rating (1-10)
  - liked (boolean)
  - watched_date
```

**Storage options:**

**Option 2A1: Keep using Parquet (2-10 users)**
```python
# Two parquet files
users = pl.read_parquet("data/users.parquet")
ratings = pl.read_parquet("data/user_ratings.parquet")

# Join for collaborative filtering
similar_users = ratings.join(users, on="user_id")
```

**Pros:**
- ✅ Simple, no infrastructure change
- ✅ Works for small groups (family/friends)
- ✅ Git versioning still works

**Cons:**
- ❌ Concurrent writes become tricky
- ❌ Manual user management
- ❌ Hard to scale beyond 10 users

**Option 2A2: Use SQLite (10-100 users)**
```python
# Single file database
import sqlite3

conn = sqlite3.connect('data/movies.db')

# Tables:
# - users
# - movies  
# - ratings (user_id, movie_id, rating, timestamp)

# Collaborative filtering query:
SELECT m.* FROM movies m
JOIN ratings r ON m.id = r.movie_id
WHERE r.user_id IN (
  -- Users similar to you
  SELECT user_id FROM ratings
  WHERE movie_id IN (YOUR_LIKED_MOVIES)
  GROUP BY user_id
  ORDER BY COUNT(*) DESC
  LIMIT 10
)
```

**Pros:**
- ✅ Better for multi-user
- ✅ ACID transactions
- ✅ SQL queries for CF
- ✅ Still a single file (easy deployment)

**Cons:**
- ❌ Lose Git versioning for data
- ❌ Need migration scripts
- ❌ More complex than Parquet

**Option 2A3: Use PostgreSQL/Supabase (100+ users)**
```python
# Full database service
# Supabase = PostgreSQL + Auth + Realtime + Storage

Tables:
- users (with auth)
- movies
- ratings
- recommendations_cache
```

**Pros:**
- ✅ Scales to thousands of users
- ✅ Built-in authentication
- ✅ Real-time updates
- ✅ Row-level security

**Cons:**
- ❌ Hosting costs ($0-25/mo)
- ❌ Much more complex
- ❌ Overkill for personal use

---

## Recommendation: Hybrid Approach ⭐

**Best of both worlds:**

1. **Use MovieLens for collaborative filtering**
   - Download MovieLens 1M dataset
   - Find "users like you" from the dataset
   - Get recommendations from those users

2. **Keep your personal Parquet data**
   - Your viewing history stays in Git
   - Single-user workflow unchanged
   - Streamlit app works as-is

3. **Combine both approaches**
   ```python
   # 50% content-based (current system)
   content_recs = content_based_model.predict(top_n=10)
   
   # 50% collaborative filtering (MovieLens)
   collab_recs = movielens_cf_model.predict(top_n=10)
   
   # Blend and re-rank
   final_recs = blend_recommendations(content_recs, collab_recs)
   ```

**Why this works:**
- ✅ Get personalized CF without collecting users
- ✅ Keep your simple architecture
- ✅ Best recommendations (hybrid > pure CF or content)
- ✅ No database migration needed
- ✅ MovieLens data refreshes yearly

---

## Implementation Plan

### Phase 1: Add MovieLens Integration (Recommended First Step)

1. Download MovieLens 1M:
   ```bash
   wget https://files.grouplens.org/datasets/movielens/ml-1m.zip
   unzip ml-1m.zip -d data/movielens/
   ```

2. Create CF model using MovieLens:
   ```python
   # scripts/recommendation/movielens_cf.py
   class MovieLensCF:
       def __init__(self):
           self.ratings = pl.read_csv("data/movielens/ratings.dat", separator="::")
           self.movies = pl.read_csv("data/movielens/movies.dat", separator="::")
       
       def find_similar_users(self, my_movies):
           # Find MovieLens users who watched similar movies
           pass
       
       def predict(self, top_n=5):
           # Get recommendations from similar users
           pass
   ```

3. Update generate_recommendations.py:
   ```python
   # Hybrid approach
   content_model = CollaborativeFilteringModel()  # Current
   movielens_model = MovieLensCF()  # New
   
   content_recs = content_model.predict(top_n=10)
   cf_recs = movielens_model.predict(top_n=10)
   
   # Blend
   final = blend_and_rerank(content_recs, cf_recs, top_n=5)
   ```

### Phase 2: (Optional) Add Real Users Later

If you want family/friends to join:

1. Add user authentication
2. Add `user_id` column to ratings
3. Use SQLite for multi-user ratings
4. Keep MovieLens as fallback

---

## Summary

**Current:** Content-based (just you)  
**Best next step:** Add MovieLens for true collaborative filtering  
**Future:** Optionally add real users with SQLite

**Storage decision:**
- **1 user:** Parquet (current) ✅
- **2-10 users:** Parquet or SQLite
- **10-100 users:** SQLite
- **100+ users:** PostgreSQL/Supabase

**For collaborative filtering NOW:**
Use MovieLens dataset - no need to collect your own users!
