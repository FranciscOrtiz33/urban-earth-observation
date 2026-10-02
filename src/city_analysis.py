from src.config import TRAINING_YEAR
from src.landcover_map import build_landcover_map
from src.landcover_model import train_city_model
from src.training_data import build_training_samples


def train_model_for_city(roi):
    """
    Train the city-specific 2021 model.
    """

    (
        samples,
        training_predictors,
        scene_count,
    ) = build_training_samples(roi)

    (
        classifier,
        training,
        test,
        confusion_matrix,
    ) = train_city_model(samples)

    return {
        "classifier": classifier,
        "training_predictors": training_predictors,
        "samples": samples,
        "training": training,
        "test": test,
        "confusion_matrix": confusion_matrix,
        "training_scene_count": scene_count,
    }


def classify_city_years(
    roi,
    classifier,
    years,
):
    """
    Apply one city's classifier to multiple years.
    """

    years = sorted(
        set(
            list(years)
            + [TRAINING_YEAR]
        )
    )

    maps = {}
    metadata = {}

    for year in years:

        (
            classified,
            scene_count,
            start_date,
            end_date,
        ) = build_landcover_map(
            roi=roi,
            classifier=classifier,
            year=year,
        )

        maps[year] = classified

        metadata[year] = {
            "scene_count": scene_count,
            "start_date": start_date,
            "end_date": end_date,
        }

    return maps, metadata