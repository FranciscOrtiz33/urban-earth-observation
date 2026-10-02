from pathlib import Path

import ee

from src.city_analysis import (
    train_model_for_city,
)
from src.config import ANALYSIS_SCALE
from src.landcover_map import (
    build_landcover_map,
)
from src.study_area import (
    load_study_area,
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
    "Training city-specific 2021 model..."
)

model = train_model_for_city(
    roi
)

classifier = model[
    "classifier"
]

print(
    "Training scenes:",
    model[
        "training_scene_count"
    ],
)

print(
    "Training samples:",
    model[
        "training"
    ]
    .size()
    .getInfo(),
)

print(
    "Test samples:",
    model[
        "test"
    ]
    .size()
    .getInfo(),
)


print(
    "\nClassifying 2021 inference period..."
)

(
    classified,
    scene_count,
    start_date,
    end_date,
) = build_landcover_map(
    roi=roi,
    classifier=classifier,
    year=2021,
)

print(
    "Inference period:",
    start_date,
    "to",
    end_date,
)

print(
    "Sentinel-2 scenes:",
    scene_count,
)

print(
    "Classification bands:",
    classified
    .bandNames()
    .getInfo(),
)

print(
    "Analysis scale:",
    ANALYSIS_SCALE,
    "m",
)


predicted_classes = (
    classified
    .sample(
        region=roi,
        scale=ANALYSIS_SCALE,
        numPixels=1000,
        seed=42,
        geometries=False,
    )
    .aggregate_histogram(
        "landcover"
    )
    .getInfo()
)

print(
    "Predicted classes:",
    predicted_classes,
)


assert (
    start_date
    == "2021-06-01"
)

assert (
    end_date
    == "2021-08-01"
)

assert (
    classified
    .bandNames()
    .getInfo()
    == ["landcover"]
)

print(
    "\nLand-cover map test passed."
)