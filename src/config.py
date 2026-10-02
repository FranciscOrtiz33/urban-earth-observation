# Spatial resolution
ANALYSIS_SCALE = 10

# Reproducibility
RANDOM_SEED = 42

# Random Forest
RF_TREES = 100

# Training
TRAINING_YEAR = 2021
TRAINING_PIXELS = 5000

# Training window:
# March 1 -> June 1 means March, April and May.
TRAINING_START_MM_DD = "06-01"
TRAINING_END_MM_DD = "08-01"

# Inference window:
# June 1 -> August 1 means June and July.
INFERENCE_START_MM_DD = "06-01"
INFERENCE_END_MM_DD = "08-01"

# Sentinel-2 scene filter
MAX_CLOUD_PERCENTAGE = 10