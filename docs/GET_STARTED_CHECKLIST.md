# Get Started Checklist ✅

Follow these steps to start getting personalized movie recommendations!

## Prerequisites
- [x] Python 3.13 installed
- [x] Virtual environment created (`.venv/`)
- [x] Dependencies installed
- [x] Movie viewing data in `data/movies_df.parquet`

## Setup Steps

### 1. Get TMDB API Key 🔑

- [ ] Go to [The Movie Database](https://www.themoviedb.org/)
- [ ] Create a free account (or log in)
- [ ] Navigate to: **Settings** → **API** → **Request an API Key**
- [ ] Choose "Developer" option
- [ ] Fill in the application form (use personal/hobby project)
- [ ] Copy your API Key (v3 auth)

### 2. Configure Environment 🔧

- [ ] Open `.env` file in the project root
- [ ] Replace `your_tmdb_api_key_here` with your actual API key:
  ```bash
  TMDB_API_KEY=abc123def456...
  ```
- [ ] Save the file

### 3. Verify Installation ✓

Run this command to check everything is installed:
```bash
source .venv/bin/activate
python -c "import sklearn, scipy, surprise, tmdbv3api; print('✓ All dependencies ready!')"
```

Expected output: `✓ All dependencies ready!`

### 4. Test the System 🧪

Generate your first recommendations:
```bash
python scripts/generate_recommendations.py
```

This will:
- ✓ Load your viewing history (last 6 months)
- ✓ Train the recommendation model
- ✓ Query TMDB for candidate movies
- ✓ Generate 5 personalized recommendations
- ✓ Save results to `data/recommendations/`

**Expected time**: 20-35 seconds

### 5. View Your Recommendations 👀

**Option A: View JSON**
```bash
cat data/recommendations/recommendations_latest.json
```

**Option B: Use Jupyter Notebook**
```bash
jupyter notebook notebooks/8_recommendation_demo.ipynb
```

**Option C: Check Parquet**
```python
import polars as pl
df = pl.read_parquet('data/recommendations/recommendations_latest.parquet')
print(df)
```

### 6. Verify Automatic Scheduling ⏰

The system is configured to retrain every **Monday at 9:17 AM**.

Check scheduled tasks:
- In Claude Code, type: `/cron-list`
- Look for job ID: `e954a988`
- Status should show: "Every Monday at 9:17 AM"

### 7. Review Documentation 📚

- [ ] Read [RECOMMENDATION_SYSTEM.md](RECOMMENDATION_SYSTEM.md) for full documentation
- [ ] Check [QUICK_START.md](QUICK_START.md) for command reference
- [ ] Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- [ ] See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details

## Troubleshooting Common Issues

### Issue: "No recommendations generated"

**Solution**:
1. Check TMDB API key is correct in `.env`
2. Verify you have at least 5 liked movies in the last 6 months:
   ```python
   import polars as pl
   from datetime import datetime, timedelta
   df = pl.read_parquet('data/movies_df.parquet')
   cutoff = datetime.now().date() - timedelta(days=180)
   recent = df.filter((pl.col('viewed') >= cutoff) & (pl.col('liked') == True))
   print(f"Recent liked movies: {len(recent)}")
   ```
3. Check internet connection

### Issue: "API rate limit exceeded"

**Solution**:
- Wait 10 seconds and retry
- TMDB allows 40 requests per 10 seconds
- System is designed to stay within limits

### Issue: "Model not found"

**Solution**:
- This is normal on first run
- Model auto-trains on first execution
- Or explicitly train: `python scripts/generate_recommendations.py`

### Issue: Can't find `.env` file

**Solution**:
```bash
# Create it manually
cat > .env << 'EOF'
OMDB_API_KEY=af6ddf50
TMDB_API_KEY=your_tmdb_key_here
EOF
```

## Next Steps

Once everything is working:

1. **Customize Parameters**
   ```bash
   # Get more recommendations
   python scripts/generate_recommendations.py --top-n 10
   
   # Use more viewing history
   python scripts/generate_recommendations.py --months-back 12
   ```

2. **Monitor Logs**
   ```bash
   # View retraining logs
   tail -f logs/retrain_latest.log
   ```

3. **Integrate with Dashboard**
   - Add recommendations to your Streamlit app
   - Display top 5 on the homepage
   - Link to TMDB for more details

4. **Provide Feedback**
   - Mark which recommendations you watch
   - Track recommendation quality over time
   - Adjust scoring weights if needed

## Success Criteria ✅

You're all set when:
- [x] TMDB API key is configured
- [x] System generates 5 recommendations successfully
- [x] Results are saved to `data/recommendations/`
- [x] Weekly schedule is active (check with `/cron-list`)
- [x] You understand how to view recommendations

## Getting Help

**Documentation**:
- Full system guide: [RECOMMENDATION_SYSTEM.md](RECOMMENDATION_SYSTEM.md)
- Quick commands: [QUICK_START.md](QUICK_START.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)

**Common Commands**:
```bash
# Generate recommendations
python scripts/generate_recommendations.py

# Manual retraining
./scripts/scheduled_retrain.sh

# Check logs
tail logs/retrain_latest.log

# Verify dependencies
python -c "import sklearn, scipy, surprise, tmdbv3api; print('OK')"
```

**Questions?**
- Check the FAQ in [RECOMMENDATION_SYSTEM.md](RECOMMENDATION_SYSTEM.md#troubleshooting)
- Review code in `scripts/recommendation/collaborative_filtering.py`
- Inspect your data: `python -c "import polars as pl; print(pl.read_parquet('data/movies_df.parquet'))"`

---

**Ready to start?** Run the test command and get your first recommendations! 🎬

```bash
python scripts/generate_recommendations.py
```
