from pathlib import Path

import ee

from src.config import ANALYSIS_SCALE
from src.landcover_labels import get_worldcover_labels
from src.study_area import load_study_area


PROJECT_ID = "elite-variety-436219-b6"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GEOJSON_PATH = PROJECT_ROOT / "data" / "study_area.geojson"


ee.Initialize(project=PROJECT_ID)

roi = load_study_area(GEOJSON_PATH)

labels = get_worldcover_labels(roi)

print("Bands:", labels.bandNames().getInfo())

print(
    "Nominal scale:",
    labels.projection().nominalScale().getInfo(),
    "m",
)

print("Analysis scale:", ANALYSIS_SCALE, "m")

print(
    "Classes in a sample:",
    labels.sample(
        region=roi,
        scale=ANALYSIS_SCALE,
        numPixels=2000,
        seed=42,
        geometries=False,
    )
    .aggregate_histogram("landcover")
    .getInfo(),
)

