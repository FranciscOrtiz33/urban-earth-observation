from pathlib import Path

import ee

from src.landcover_model import (
    train_city_model,
)
from src.study_area import (
    load_study_area,
)
from src.training_data import (
    build_training_samples,
)


PROJECT_ID = "elite-variety-436219-b6"

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

GEOJSON_PATH = (
    PROJECT_ROOT
    / "data"
    / "study_area.geojson"
)


ee.Initialize(
    project=PROJECT_ID
)

roi = load_study_area(
    GEOJSON_PATH
)


print(
    "Building 2021 training samples..."
)

(
    samples,
    predictors,
    scene_count,
) = build_training_samples(
    roi=roi
)


print(
    "Sentinel-2 training scenes:",
    scene_count,
)

print(
    "Total samples:",
    samples
    .size()
    .getInfo(),
)

print(
    "Samples by class:",
    samples
    .aggregate_histogram(
        "landcover"
    )
    .getInfo(),
)


print(
    "\nTraining city-specific Random Forest..."
)

(
    classifier,
    training_samples,
    test_samples,
    confusion_matrix,
) = train_city_model(
    samples
)


training_count = (
    training_samples
    .size()
    .getInfo()
)

test_count = (
    test_samples
    .size()
    .getInfo()
)


print(
    "Training samples:",
    training_count,
)

print(
    "Test samples:",
    test_count,
)

print(
    "Training samples by class:",
    training_samples
    .aggregate_histogram(
        "landcover"
    )
    .getInfo(),
)

print(
    "Test samples by class:",
    test_samples
    .aggregate_histogram(
        "landcover"
    )
    .getInfo(),
)


matrix_values = (
    confusion_matrix
    .array()
    .getInfo()
)

print(
    "\nConfusion matrix:"
)

for row in matrix_values:
    print(row)


accuracy = (
    confusion_matrix
    .accuracy()
    .getInfo()
)

kappa = (
    confusion_matrix
    .kappa()
    .getInfo()
)


print(
    "\nOverall accuracy:",
    accuracy,
)

print(
    "Kappa:",
    kappa,
)


assert training_count > 0
assert test_count > 0

assert len(
    matrix_values
) == 4

assert all(
    len(row) == 4
    for row in matrix_values
)

assert 0 <= accuracy <= 1
assert -1 <= kappa <= 1


print(
    "\nLand-cover model test passed."
)