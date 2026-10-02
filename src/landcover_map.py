from src.config import (
    INFERENCE_END_MM_DD,
    INFERENCE_START_MM_DD,
)
from src.predictors import (
    INPUT_BANDS,
    build_predictor_stack,
)


def build_landcover_map(
    roi,
    classifier,
    year,
):
    """
    Apply the city's 2021-trained classifier to one
    inference year.

    The classifier is trained separately using the 2021
    March-May training dataset. Temporal inference uses
    the June-July window for every classified year,
    including 2021.
    """

    start_date = (
        f"{year}-"
        f"{INFERENCE_START_MM_DD}"
    )

    end_date = (
        f"{year}-"
        f"{INFERENCE_END_MM_DD}"
    )

    predictors, scene_count = (
        build_predictor_stack(
            roi=roi,
            start_date=start_date,
            end_date=end_date,
        )
    )

    classified = (
        predictors
        .select(INPUT_BANDS)
        .classify(classifier)
        .rename("landcover")
        .toByte()
        .clip(roi)
    )

    return (
        classified,
        scene_count,
        start_date,
        end_date,
    )