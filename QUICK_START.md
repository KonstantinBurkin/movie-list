# Quick Start - Movie Recommendations

## 1. Setup (One Time)

```bash
# Get TMDB API key from https://www.themoviedb.org/settings/api
# Add to .env file:
echo "TMDB_API_KEY=your_key_here" >> .env

# Run setup
./scripts/setup_recommendations.sh
```

## 2. Generate Recommendations

```bash
# Generate 5 recommendations using last 6 months of data
python scripts/generate_recommendations.py

# More options:
python scripts/generate_recommendations.py --top-n 10    # Get 10 recommendations
python scripts/generate_recommendations.py --months-back 12  # Use 12 months of data
python scripts/generate_recommendations.py --no-retrain  # Skip retraining
```

## 3. View Results

```bash
# JSON output
cat data/recommendations/recommendations_latest.json

# Or use the Jupyter notebook
jupyter notebook notebooks/8_recommendation_demo.ipynb
```

## 4. Automatic Updates

✅ **Already configured!** The system retrains every **Monday at 9:17 AM**

Check logs:
```bash
tail -f logs/retrain_latest.log
```

## Command Reference

| Command | Purpose |
|---------|---------|
| `python scripts/generate_recommendations.py` | Generate new recommendations |
| `./scripts/scheduled_retrain.sh` | Manually trigger weekly retraining |
| `./scripts/setup_recommendations.sh` | First-time setup |
| `/cron-list` (in Claude Code) | Check scheduled tasks |

## What You Get

Each recommendation includes:
- 🎬 Title and year
- ⭐ IMDB rating
- 📊 Match score (how well it fits your taste)
- 📝 Overview/synopsis
- 🎨 Poster image link

## Troubleshooting

**No recommendations?**
- Check TMDB API key in `.env`
- Need at least 5 liked movies in last 6 months

**Want to change schedule?**
- Edit `scripts/scheduled_retrain.sh`
- Update cron job in Claude Code with `/cron-list`

---

📖 Full docs: [RECOMMENDATION_SYSTEM.md](RECOMMENDATION_SYSTEM.md)
