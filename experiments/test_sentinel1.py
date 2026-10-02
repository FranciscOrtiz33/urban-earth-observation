from pathlib import Path

import ee

from src.sentinel1 import build_sentinel1_composite
from src.study_area import load_study_area

PROJECT_ID = "elite-variety-436219-b6"

BASE_DIR = Path(__file__).resolve().parent

GEOJSON_PATH = (
    BASE_DIR / "data" / "study_area.geojson"
)

ee.Initialize(project=PROJECT_ID)

roi = load_study_area(GEOJSON_PATH)

sar, scene_count = build_sentinel1_composite(
    roi=roi,
    start_date="2021-03-01",
    end_date="2021-06-01",
)

print("Sentinel-1 scenes:", scene_count)

print(
    "SAR bands:",
    sar.bandNames().getInfo(),
)

stats = sar.reduceRegion(
    reducer=ee.Reducer.percentile(
        [2, 25, 50, 75, 98]
    ),
    geometry=roi,
    scale=10,
    maxPixels=1e10,
    tileScale=4,
).getInfo()

print("SAR percentiles:")

for key, value in stats.items():
    print(f"{key}: {value:.2f} dB")