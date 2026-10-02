from pathlib import Path

import ee

from src.sentinel2 import build_sentinel2_composite
from src.study_area import load_study_area


PROJECT_ID = "elite-variety-436219-b6"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GEOJSON_PATH = (
    PROJECT_ROOT
    / "data"
    / "study_area.geojson"
)


ee.Initialize(project=PROJECT_ID)

roi = load_study_area(GEOJSON_PATH)

composite, scene_count = build_sentinel2_composite(
    roi=roi,
    start_date="2025-03-01",
    end_date="2025-06-01",
)

print("Sentinel-2 scenes:", scene_count)
print("Composite bands:", composite.bandNames().getInfo())