import hashlib
import tempfile
from pathlib import Path

import ee

from src.city_analysis import (
    classify_city_years,
    train_model_for_city,
)
from src.city_search import create_city_study_area
from src.landcover_statistics import (
    calculate_gains_losses,
    calculate_multiyear_areas,
    calculate_net_changes,
    calculate_period_transition,
)
from src.study_area import load_study_area


def initialize_analysis_state(session_state):
    """
    Ensure the Streamlit session contains the caches used
    by the land-cover workflow.
    """

    session_state.setdefault(
        "landcover_models",
        {},
    )

    session_state.setdefault(
        "thermal_landcover_results",
        {},
    )


def get_area_signature(
    area_mode,
    uploaded_file,
    selected_city,
    radius_km,
):
    """
    Build a stable identifier for the selected study area.

    Inference years are intentionally excluded so the same
    city-specific 2021 model can be reused for new year sets.
    """

    if area_mode == "Upload GeoJSON":
        if uploaded_file is None:
            return None

        file_hash = hashlib.sha256(
            uploaded_file.getvalue()
        ).hexdigest()

        raw_signature = (
            "geojson",
            file_hash,
        )

    else:
        if selected_city is None:
            return None

        raw_signature = (
            "city",
            selected_city["name"],
            selected_city["latitude"],
            selected_city["longitude"],
            radius_km,
        )

    return hashlib.sha256(
        repr(raw_signature).encode(
            "utf-8"
        )
    ).hexdigest()


def build_study_area(
    area_mode,
    uploaded_file,
    selected_city,
    radius_km,
):
    """
    Build the Earth Engine ROI from either an uploaded
    GeoJSON or a searched city with a circular radius.
    """

    if area_mode == "Upload GeoJSON":
        if uploaded_file is None:
            raise ValueError(
                "A GeoJSON file is required."
            )

        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".geojson",
            delete=False,
        ) as temp_file:
            temp_file.write(
                uploaded_file.getvalue()
            )

            temp_path = Path(
                temp_file.name
            )

        try:
            return load_study_area(
                temp_path
            )
        finally:
            temp_path.unlink(
                missing_ok=True
            )

    if selected_city is None:
        raise ValueError(
            "A city must be selected first."
        )

    return create_city_study_area(
        latitude=selected_city[
            "latitude"
        ],
        longitude=selected_city[
            "longitude"
        ],
        radius_km=radius_km,
    )


def _build_model_metrics(model):
    """
    Convert Earth Engine model-evaluation objects into
    values that can be stored and displayed by Streamlit.
    """

    matrix = model[
        "confusion_matrix"
    ]

    return {
        "accuracy":
            matrix
            .accuracy()
            .getInfo(),
        "kappa":
            matrix
            .kappa()
            .getInfo(),
        "matrix":
            matrix
            .array()
            .getInfo(),
        "training_samples":
            model[
                "training"
            ]
            .size()
            .getInfo(),
        "test_samples":
            model[
                "test"
            ]
            .size()
            .getInfo(),
        "training_scenes":
            model[
                "training_scene_count"
            ],
    }


def get_or_train_city_model(
    session_state,
    area_signature,
    roi,
):
    """
    Reuse the model cached for this study area, or train
    its city-specific 2021 Random Forest the first time.
    """

    models = session_state[
        "landcover_models"
    ]

    model_reused = (
        area_signature in models
    )

    if not model_reused:
        model = train_model_for_city(
            roi
        )

        models[
            area_signature
        ] = {
            "classifier":
                model[
                    "classifier"
                ],
            "metrics":
                _build_model_metrics(
                    model
                ),
        }

    return (
        models[
            area_signature
        ],
        model_reused,
    )


def run_landcover_analysis(
    session_state,
    project_id,
    area_signature,
    area_mode,
    uploaded_file,
    selected_city,
    radius_km,
    selected_years,
):
    """
    Run the complete land-cover workflow for the selected
    study area and years.

    The function:
    1. Initializes Earth Engine.
    2. Builds the ROI.
    3. Trains or reuses the city-specific 2021 model.
    4. Classifies all requested years.
    5. Calculates areas and land-cover changes.
    6. Stores the complete result in session state.
    """

    initialize_analysis_state(
        session_state
    )

    ee.Initialize(
        project=project_id
    )

    roi = build_study_area(
        area_mode=area_mode,
        uploaded_file=uploaded_file,
        selected_city=selected_city,
        radius_km=radius_km,
    )

    (
        city_model,
        model_reused,
    ) = get_or_train_city_model(
        session_state=session_state,
        area_signature=area_signature,
        roi=roi,
    )

    maps, metadata = (
        classify_city_years(
            roi=roi,
            classifier=city_model[
                "classifier"
            ],
            years=selected_years,
        )
    )

    areas = calculate_multiyear_areas(
        classified_maps=maps,
        roi=roi,
    )

    (
        transition_start,
        transition_end,
        transition_matrix,
    ) = calculate_period_transition(
        classified_maps=maps,
        roi=roi,
    )

    (
        change_start,
        change_end,
        net_changes,
    ) = calculate_net_changes(
        multiyear_areas=areas,
    )

    gains_losses = (
        calculate_gains_losses(
            transition_matrix
        )
    )

    result_signature = (
        area_signature,
        tuple(
            sorted(
                selected_years
            )
        ),
    )

    result = {
        "signature":
            result_signature,
        "roi":
            roi,
        "maps":
            maps,
        "metadata":
            metadata,
        "areas":
            areas,
        "transition_start":
            transition_start,
        "transition_end":
            transition_end,
        "transition_matrix":
            transition_matrix,
        "change_start":
            change_start,
        "change_end":
            change_end,
        "net_changes":
            net_changes,
        "gains_losses":
            gains_losses,
        "metrics":
            city_model[
                "metrics"
            ],
    }

    session_state[
        "landcover_result"
    ] = result

    return result, model_reused
