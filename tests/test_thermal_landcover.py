from pathlib import Path

import ee

from src.city_analysis import (
    classify_city_years,
    train_model_for_city,
)
from src.study_area import load_study_area
from src.thermal_landcover import (
    analyze_year_temperature_by_class,
)


PROJECT_ID = "elite-variety-436219-b6"

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GEOJSON_PATH = (
   PROJECT_ROOT / "data" / "study_area.geojson"
)


ee.Initialize(
    project=PROJECT_ID
)

roi = load_study_area(
    GEOJSON_PATH
)


# ---------------------------------------------
# Train city-specific model
# ---------------------------------------------

print("Training city model...")

model = train_model_for_city(
    roi
)


# ---------------------------------------------
# Classify one year
# ---------------------------------------------

YEAR = 2025

maps, metadata = classify_city_years(
    roi=roi,
    classifier=model["classifier"],
    years=[YEAR],
)

classified_image = maps[YEAR]


# ---------------------------------------------
# LST by land-cover class
# ---------------------------------------------

print(
    f"\nCalculating LST by land cover for {YEAR}..."
)

thermal = (
    analyze_year_temperature_by_class(
        roi=roi,
        classified_image=classified_image,
        year=YEAR,
    )
)

print(
    "Landsat scenes:",
    thermal["scene_count"],
)

print(
    "Period:",
    thermal["start_date"],
    "to",
    thermal["end_date"],
)


for class_name, stats in thermal[
    "statistics"
].items():

    print(
        f"\n{class_name}"
    )

    print(
        f"Mean: "
        f"{stats['mean_c']:.2f} °C"
    )

    print(
        f"Median: "
        f"{stats['median_c']:.2f} °C"
    )

    print(
        f"Minimum: "
        f"{stats['min_c']:.2f} °C"
    )

    print(
        f"Maximum: "
        f"{stats['max_c']:.2f} °C"
    )

    print(
        f"Valid pixels: "
        f"{stats['valid_pixels']:,}"
    )