from pathlib import Path

from src.landcover_statistics import (
    calculate_multiyear_areas,
    calculate_period_transition,
    calculate_net_changes,
    calculate_gains_losses,
)

import ee

from src.city_analysis import (
    classify_city_years,
    train_model_for_city,
)
from src.study_area import load_study_area


PROJECT_ID = "elite-variety-436219-b6"

PROJECT_ROOT = Path(__file__).resolve().parents[1]

GEOJSON_PATH = (
    PROJECT_ROOT / "data" / "study_area.geojson"
)


ee.Initialize(project=PROJECT_ID)

roi = load_study_area(
    GEOJSON_PATH
)

print("Training city model...")

model = train_model_for_city(
    roi
)

matrix = model[
    "confusion_matrix"
]

print(
    "Training samples:",
    model["training"].size().getInfo(),
)

print(
    "Test samples:",
    model["test"].size().getInfo(),
)

print(
    "Training scenes:",
    model["training_scene_count"],
)

print("\nConfusion matrix:")

for row in matrix.array().getInfo():
    print(row)

print(
    "\nOverall accuracy:",
    matrix.accuracy().getInfo(),
)

print(
    "Kappa:",
    matrix.kappa().getInfo(),
)

print("\nRunning temporal inference...")

maps, metadata = classify_city_years(
    roi=roi,
    classifier=model["classifier"],
    years=[
        2018,
        2021,
        2025,
    ],
)

for year in sorted(maps):

    print(
        year,
        metadata[year],
        maps[year].bandNames().getInfo(),
    )

print("\nCalculating land-cover areas...")

areas = calculate_multiyear_areas(
    classified_maps=maps,
    roi=roi,
)

for year in sorted(areas):

    print(f"\n{year}")

    for class_name, hectares in areas[year].items():

        print(
            f"{class_name}: "
            f"{hectares:,.2f} ha"
        )

print("\nCalculating transition matrix...")

start_year, end_year, transition_matrix = (
    calculate_period_transition(
        classified_maps=maps,
        roi=roi,
    )
)

print(
    f"\nTransition matrix: "
    f"{start_year} -> {end_year}"
)

class_names = list(
    transition_matrix.keys()
)

print(
    "\nFrom / To".ljust(35),
    end="",
)

for class_name in class_names:
    print(
        class_name[:12].rjust(15),
        end="",
    )

print()

for start_class in class_names:

    print(
        start_class.ljust(35),
        end="",
    )

    for end_class in class_names:

        value = (
            transition_matrix[
                start_class
            ][
                end_class
            ]
        )

        print(
            f"{value:,.2f}".rjust(15),
            end="",
        )

    print()

print("\nCalculating net changes...")

start_year, end_year, changes = (
    calculate_net_changes(
        multiyear_areas=areas,
    )
)

print(
    f"\nNet change: "
    f"{start_year} -> {end_year}"
)

for class_name, values in changes.items():

    print(
        f"\n{class_name}"
    )

    print(
        f"Start: "
        f"{values['start_area_ha']:,.2f} ha"
    )

    print(
        f"End: "
        f"{values['end_area_ha']:,.2f} ha"
    )

    print(
        f"Change: "
        f"{values['change_ha']:+,.2f} ha"
    )

    if values["change_percent"] is not None:

        print(
            f"Change (%): "
            f"{values['change_percent']:+.2f}%"
        )


print("\nCalculating gains and losses...")

gains_losses = calculate_gains_losses(
    transition_matrix
)

for class_name, values in gains_losses.items():

    print(f"\n{class_name}")

    print(
        f"Stable: "
        f"{values['stable_ha']:,.2f} ha"
    )

    print(
        f"Gains: "
        f"{values['gains_ha']:,.2f} ha"
    )

    print(
        f"Losses: "
        f"{values['losses_ha']:,.2f} ha"
    )

    print(
        f"Net: "
        f"{values['net_change_ha']:+,.2f} ha"
    )