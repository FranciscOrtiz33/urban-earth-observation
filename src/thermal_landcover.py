import ee

from src.config import (
    ANALYSIS_SCALE,
    INFERENCE_START_MM_DD,
    INFERENCE_END_MM_DD,
)
from src.landcover_statistics import CLASS_NAMES
from src.lst import build_lst_composite


def build_year_lst(
    roi,
    year,
):
    """
    Build the LST composite for the same seasonal
    window used by land-cover inference.
    """

    start_date = (
        f"{year}-"
        f"{INFERENCE_START_MM_DD}"
    )

    end_date = (
        f"{year}-"
        f"{INFERENCE_END_MM_DD}"
    )

    lst_image, scene_count = build_lst_composite(
        roi=roi,
        start_date=start_date,
        end_date=end_date,
    )

    return (
        lst_image,
        scene_count,
        start_date,
        end_date,
    )


def calculate_lst_by_landcover(
    lst_image,
    classified_image,
    roi,
):
    """
    Calculate LST statistics for each
    land-cover class.
    """

    classes = (
        classified_image
        .rename("landcover")
        .toByte()
    )

    combined = (
        lst_image
        .rename("LST_C")
        .addBands(classes)
    )

    reducer = (
        ee.Reducer.mean()
        .combine(
            reducer2=ee.Reducer.median(),
            sharedInputs=True,
        )
        .combine(
            reducer2=ee.Reducer.minMax(),
            sharedInputs=True,
        )
        .combine(
            reducer2=ee.Reducer.count(),
            sharedInputs=True,
        )
        .group(
            groupField=1,
            groupName="class",
        )
    )

    result = combined.reduceRegion(
        reducer=reducer,
        geometry=roi,
        scale=ANALYSIS_SCALE,
        maxPixels=1e13,
        tileScale=4,
    ).getInfo()

    statistics = {}

    for group in result.get("groups", []):

        class_value = int(
            group["class"]
        )

        if class_value not in CLASS_NAMES:
            continue

        class_name = CLASS_NAMES[
            class_value
        ]

        statistics[class_name] = {
            "mean_c":
                group.get("mean"),

            "median_c":
                group.get("median"),

            "min_c":
                group.get("min"),

            "max_c":
                group.get("max"),

            "valid_pixels":
                group.get("count"),
        }

    return statistics


def analyze_year_temperature_by_class(
    roi,
    classified_image,
    year,
):
    """
    Run LST analysis for one classified year.
    """

    (
        lst_image,
        scene_count,
        start_date,
        end_date,
    ) = build_year_lst(
        roi=roi,
        year=year,
    )

    statistics = (
        calculate_lst_by_landcover(
            lst_image=lst_image,
            classified_image=classified_image,
            roi=roi,
        )
    )

    return {
        "lst_image": lst_image,
        "scene_count": scene_count,
        "start_date": start_date,
        "end_date": end_date,
        "statistics": statistics,
    }

def analyze_multiyear_temperature_by_class(
    roi,
    classified_maps,
):
    """
    Calculate LST statistics by land-cover class
    for multiple classified years.

    Parameters
    ----------
    roi : ee.Geometry
        Study area.

    classified_maps : dict
        Dictionary in the form:
        {
            year: classified_image
        }

    Returns
    -------
    dict
        Thermal analysis for each year.
    """

    results = {}

    for year in sorted(classified_maps.keys()):

        results[year] = (
            analyze_year_temperature_by_class(
                roi=roi,
                classified_image=classified_maps[year],
                year=year,
            )
        )

    return results