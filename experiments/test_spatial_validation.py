from pathlib import Path

import ee

from src.study_area import load_study_area
from src.training_data import build_training_samples
from src.spatial_validation import (
    train_with_spatial_validation,
)


PROJECT_ID = "elite-variety-436219-b6"

BASE_DIR = Path(__file__).resolve().parent

GEOJSON_PATH = (
    BASE_DIR / "data" / "study_area.geojson"
)


ee.Initialize(project=PROJECT_ID)

roi = load_study_area(GEOJSON_PATH)

samples, s2_count, s1_count = build_training_samples(
    roi=roi,
    start_date="2021-03-01",
    end_date="2021-06-01",
    samples_per_class=1000,
)

(
    classifier,
    training,
    validation,
    confusion_matrix,
) = train_with_spatial_validation(
    samples=samples,
    block_size_m=1000,
    number_of_trees=100,
)

print(
    "Training samples:",
    training.size().getInfo(),
)

print(
    "Validation samples:",
    validation.size().getInfo(),
)

print(
    "Training by class:",
    training.aggregate_histogram(
        "landcover"
    ).getInfo(),
)

print(
    "Validation by class:",
    validation.aggregate_histogram(
        "landcover"
    ).getInfo(),
)

print("\nConfusion matrix:")

for row in confusion_matrix.array().getInfo():
    print(row)

print(
    "\nOverall accuracy:",
    confusion_matrix.accuracy().getInfo(),
)

print(
    "Kappa:",
    confusion_matrix.kappa().getInfo(),
)

print("Sentinel-2 scenes:", s2_count)
print("Sentinel-1 scenes:", s1_count)