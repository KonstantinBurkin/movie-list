"""Configurations"""

from pathlib import Path

# Data directories
MOVIELENS_DATA_DIR = Path("data/movielens")
MOVIES_DF_PATH = Path("data/movies_df.parquet")
RECOMMENDATIONS_DIR = Path("data/recommendations")

# Model cache directory
MODEL_DIR = Path("models")

# ALS hyperparameters
ALS_FACTORS = 64
ALS_REGULARIZATION = 0.05
ALS_ITERATIONS = 15
