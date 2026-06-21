#!/bin/bash
# Weekly retraining script for movie recommendation system

set -e

PROJECT_DIR="/Users/konstantin/Documents/projects/movie-list"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/retrain_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

echo "========================================" | tee -a "$LOG_FILE"
echo "Movie Recommendation System - Weekly Retrain" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

cd "$PROJECT_DIR"

source .venv/bin/activate

echo "Running recommendation generation with retraining..." | tee -a "$LOG_FILE"

python scripts/generate_recommendations.py --top-n 5 --months-back 6 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?

echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Completed at: $(date)" | tee -a "$LOG_FILE"
echo "Exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

if [ -f "$LOG_DIR/retrain_latest.log" ]; then
    rm "$LOG_DIR/retrain_latest.log"
fi
ln -s "$LOG_FILE" "$LOG_DIR/retrain_latest.log"

exit $EXIT_CODE
