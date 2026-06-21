# Streamlit Dashboard - Recommendations Feature

Documentation for the recommendations section in the Streamlit dashboard.

## Overview

The Streamlit dashboard now displays AI-powered movie recommendations right after the watched movies table, providing personalized suggestions based on your viewing history.

## Features

### 🎯 Recommendations Display

**Location**: Between the watched movies table and analytics charts

**Information Shown**:
- Movie title and year
- IMDB rating
- Match score (how well it fits your preferences)
- Movie poster image
- Full description/overview
- Generation timestamp

**Layout**:
```
┌─────────────────────────────────────────────┐
│  🎯 Recommended Movies for You              │
│  Generated on [Date] • Based on last 6 mos  │
├─────────────────────────────────────────────┤
│  1. Movie Title (Year)          [Poster]    │
│     Rating: 8.5/10                          │
│     Match Score: 7.8                        │
│     Year: 2023                              │
│     📝 Description (expandable)             │
├─────────────────────────────────────────────┤
│  2. Another Movie (Year)        [Poster]    │
│     ...                                     │
└─────────────────────────────────────────────┘
```

### 📊 Metrics Displayed

For each recommendation:

1. **Rating** - IMDB rating out of 10
2. **Match Score** - Algorithm confidence (0-10)
3. **Year** - Release year
4. **Description** - Full movie overview (expandable)
5. **Poster** - Movie poster image from TMDB

### ℹ️ How It Works Section

Expandable section explaining:
- Collaborative filtering algorithm
- Weight breakdown (Genre 40%, Rating 30%, Year 20%, Popularity 10%)
- Retraining schedule
- Link to full documentation

## Running the Dashboard

### Start Locally

```bash
# Activate virtual environment
source .venv/bin/activate

# Run Streamlit
streamlit run scripts/streamlit_app.py
```

**Access at**: http://localhost:8501

### Deploy to Streamlit Cloud

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your repository
4. Deploy from `scripts/streamlit_app.py`

**Secrets Configuration**:
Add to Streamlit Cloud secrets:
```toml
TMDB_API_KEY = "your_key_here"
```

## Data Source

The dashboard reads recommendations from:
```
data/recommendations/recommendations_latest.json
```

**Format**:
```json
{
  "generated_at": "2026-06-21T14:04:14.123456",
  "months_back": 6,
  "recommendations": [
    {
      "title": "Movie Title",
      "year": 2023,
      "tmdb_id": 12345,
      "rating": 8.5,
      "genres": [28, 18],
      "overview": "Description...",
      "score": 7.8,
      "poster_path": "/path.jpg"
    }
  ]
}
```

## Edge Cases Handled

### No Recommendations File

**Display**:
```
⚠️ No recommendations found

Recommendations will appear here once generated. To create recommendations:
1. Ensure your TMDB API key is configured in .env
2. Run: python scripts/generate_recommendations.py
3. Reload this page
```

### Empty Recommendations

**Display**:
```
ℹ️ No recommendations available yet. Run the recommendation system to generate suggestions!

🚀 How to generate recommendations
[Code snippet with instructions]
```

### Error Loading

**Display**:
```
❌ Error loading recommendations: [error message]
ℹ️ Please ensure the recommendation system has been run at least once.
```

## Customization

### Change Number of Recommendations Shown

**In `generate_recommendations.py`**:
```bash
python scripts/generate_recommendations.py --top-n 10
```

**In Dashboard**:
The dashboard shows all recommendations in the JSON file.

### Modify Layout

**Edit `scripts/streamlit_app.py`**:

```python
# Change column ratio (default: 3:1)
col1, col2 = st.columns([3, 1])  # Change to [2, 1] or [4, 1]

# Change which description is expanded by default
with st.expander("📝 Description", expanded=(i == 1)):  # First only
# or
with st.expander("📝 Description", expanded=True):  # All expanded
```

### Add More Metadata

**Example - Add Director**:

1. Update `generate_recommendations.py` to include director:
```python
recommendations.append({
    # ... existing fields ...
    'director': director_name,  # Add this
})
```

2. Update `streamlit_app.py`:
```python
# Display director
if rec.get('director'):
    st.text(f"🎬 Directed by {rec['director']}")
```

## Styling

### Current Style

- **Header**: Large, bold with emoji
- **Cards**: Clean white cards with subtle borders
- **Metrics**: Streamlit's built-in metric cards
- **Posters**: Responsive images from TMDB
- **Expandable sections**: For descriptions and info

### Custom CSS (Optional)

Add to `streamlit_app.py`:
```python
st.markdown("""
<style>
    .recommendation-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)
```

## Performance

### Load Time

- **Recommendation loading**: < 100ms
- **Image loading**: Async from TMDB CDN
- **Total overhead**: Minimal (~200ms)

### Optimization Tips

1. **Cache recommendations**:
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_recommendations():
    with open(recommendations_path, "r") as f:
        return json.load(f)
```

2. **Lazy load images**:
Images are already lazy-loaded by Streamlit

3. **Limit recommendations**:
```python
recommendations = rec_data.get("recommendations", [])[:5]  # First 5 only
```

## Troubleshooting

### Issue: Recommendations not showing

**Check**:
1. File exists: `ls data/recommendations/recommendations_latest.json`
2. Valid JSON: `cat data/recommendations/recommendations_latest.json | jq`
3. Streamlit can read it: Check file permissions

**Fix**:
```bash
# Generate recommendations
python scripts/generate_recommendations.py

# Verify file created
ls -lh data/recommendations/recommendations_latest.json

# Restart Streamlit
streamlit run scripts/streamlit_app.py
```

### Issue: Images not loading

**Cause**: TMDB CDN or missing poster_path

**Fix**: Check if `poster_path` exists in JSON:
```bash
cat data/recommendations/recommendations_latest.json | jq '.recommendations[0].poster_path'
```

### Issue: Old recommendations showing

**Cause**: Cached data

**Fix**:
1. Clear Streamlit cache: Press `C` in browser
2. Regenerate recommendations: `python scripts/generate_recommendations.py`

### Issue: Slow loading

**Cause**: Too many images

**Fix**: Limit recommendations or implement pagination:
```python
# Show only first 5
recommendations = recommendations[:5]
```

## Future Enhancements

Potential improvements:

- [ ] Add "Mark as watched" button
- [ ] Filter recommendations by genre
- [ ] Show similar movies to recommendations
- [ ] Add recommendation history
- [ ] Display confidence intervals
- [ ] Show why each movie was recommended
- [ ] Add feedback mechanism
- [ ] Implement A/B testing for algorithms
- [ ] Show recommendation trends over time
- [ ] Export recommendations to CSV

## Example Output

**Live Dashboard**: https://kburkin-movie-list.streamlit.app/

**Local Preview**:
```bash
streamlit run scripts/streamlit_app.py
```

**Screenshot Layout**:
```
+--------------------------------------+
| 🎬 My Movie Dashboard                |
+--------------------------------------+
| [Filter: liked?]                     |
| [Watched Movies Table]               |
+--------------------------------------+
| 🎯 Recommended Movies for You        |
| Generated on June 21, 2026           |
|                                      |
| 1. Princes and Princesses (2000)     |
|    ⭐ 7.7/10  🎯 2.71  📅 2000      |
|    [Poster]  [Description...]        |
|                                      |
| 2. Mind Game (2004)                  |
|    ⭐ 7.5/10  🎯 2.70  📅 2004      |
|    [Poster]  [Description...]        |
+--------------------------------------+
| 📊 Movie Analytics                   |
| [Charts and graphs...]               |
+--------------------------------------+
```

## Related Documentation

- [Recommendation System Guide](RECOMMENDATION_SYSTEM.md)
- [Architecture](ARCHITECTURE.md)
- [Quick Start](QUICK_START.md)

---

**Last Updated**: 2026-06-21  
**Version**: 1.0.0
