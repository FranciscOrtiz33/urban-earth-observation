from pathlib import Path

import ee

from src.config import (
    TRAINING_PIXELS,
)
from src.predictors import (
    INPUT_BANDS,
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
    "Building city-specific 2021 training dataset..."
)

(
    samples,
    predictors,
    scene_count,
) = build_training_samples(
    roi=roi
)


total_samples = (
    samples
    .size()
    .getInfo()
)

samples_by_class = (
    samples
    .aggregate_histogram(
        "landcover"
    )
    .getInfo()
)

sample_properties = (
    samples
    .first()
    .propertyNames()
    .getInfo()
)

predictor_bands = (
    predictors
    .bandNames()
    .getInfo()
)


print(
    "Sentinel-2 training scenes:",
    scene_count,
)

print(
    "Requested training pixels:",
    TRAINING_PIXELS,
)

print(
    "Total samples:",
    total_samples,
)

print(
    "Samples by class:",
    samples_by_class,
)

print(
    "Predictor bands:",
    predictor_bands,
)

print(
    "Sample properties:",
    sample_properties,
)


# --------------------------------------------------
# Basic validation
# --------------------------------------------------

assert scene_count > 0

assert total_samples > 0

assert total_samples <= TRAINING_PIXELS

assert "landcover" in sample_properties

assert "random" in sample_properties


for band in INPUT_BANDS:

    assert band in predictor_bands

    assert band in sample_properties


class_values = {
    int(class_value)
    for class_value
    in samples_by_class.keys()
}

assert class_values.issubset(
    {1, 2, 3, 4}
)

assert len(class_values) > 1


print(
    "\nTraining-data test passed."
)