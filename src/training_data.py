import ee

from src.config import (
    ANALYSIS_SCALE,
    RANDOM_SEED,
    TRAINING_END_MM_DD,
    TRAINING_PIXELS,
    TRAINING_START_MM_DD,
    TRAINING_YEAR,
)
from src.landcover_labels import (
    get_worldcover_labels,
)
from src.predictors import (
    INPUT_BANDS,
    build_predictor_stack,
)


def build_training_samples(roi):
    """
    Build the city-specific 2021 training dataset.

    The model is trained once per city using:
    - Sentinel-2 2021
    - Spectral indices
    - SRTM
    - ESA WorldCover 2021
    """

    start_date = (
        f"{TRAINING_YEAR}-"
        f"{TRAINING_START_MM_DD}"
    )

    end_date = (
        f"{TRAINING_YEAR}-"
        f"{TRAINING_END_MM_DD}"
    )

    predictors, scene_count = (
        build_predictor_stack(
            roi=roi,
            start_date=start_date,
            end_date=end_date,
        )
    )

    labels = get_worldcover_labels(roi)

    training_image = (
        predictors
        .select(INPUT_BANDS)
        .addBands(labels)
    )

    # Reference 10 m Sentinel-2 grid.
    reference_image = (
        ee.ImageCollection(
            "COPERNICUS/S2_SR_HARMONIZED"
        )
        .filterBounds(roi)
        .filterDate(
            start_date,
            end_date,
        )
        .first()
    )

    reference_projection = (
        ee.Image(reference_image)
        .select("B2")
        .projection()
    )

    samples = (
        training_image
        .sample(
            region=roi,
            scale=ANALYSIS_SCALE,
            projection=reference_projection,
            numPixels=TRAINING_PIXELS,
            seed=RANDOM_SEED,
            tileScale=4,
            geometries=False,
        )
        .randomColumn(
            columnName="random",
            seed=RANDOM_SEED,
        )
    )

    return (
        samples,
        predictors,
        scene_count,
    )