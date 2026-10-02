from pathlib import Path

import ee

from src.city_analysis import (
    classify_city_years,
    train_model_for_city,
)
from src.study_area import load_study_area
from src.thermal_landcover import (
    analyze_multiyear_temperature_by_class,
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
# Train the city-specific model
# ---------------------------------------------

print("Training city model...")

model = train_model_for_city(
    roi
)


# ---------------------------------------------
# Classify multiple years
# ---------------------------------------------

years = [
    2018,
    2021,
    2025,
]

print(
    "\nClassifying years:",
    years,
)

maps, metadata = classify_city_years(
    roi=roi,
    classifier=model["classifier"],
    years=years,
)


# ---------------------------------------------
# Thermal analysis
# ---------------------------------------------

print(
    "\nCalculating multiyear thermal behavior..."
)

thermal_results = (
    analyze_multiyear_temperature_by_class(
        roi=roi,
        classified_maps=maps,
    )
)


for year in sorted(thermal_results):

    result = thermal_results[year]

    print("\n" + "=" * 50)

    print(
        f"{year}"
    )

    print(
        f"Landsat scenes: "
        f"{result['scene_count']}"
    )

    print(
        f"Period: "
        f"{result['start_date']} "
        f"to "
        f"{result['end_date']}"
    )

    for class_name, stats in result[
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