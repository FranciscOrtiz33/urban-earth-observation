from pathlib import Path

import ee

from src.predictors import (
    BASE_INPUT_BANDS,
    INPUT_BANDS,
)
from src.spatial_validation import assign_spatial_blocks
from src.study_area import load_study_area
from src.training_data import build_training_samples

PROJECT_ID = "elite-variety-436219-b6"

BASE_DIR = Path(__file__).resolve().parent
GEOJSON_PATH = BASE_DIR / "data" / "study_area.geojson"

ee.Initialize(project=PROJECT_ID)

roi = load_study_area(GEOJSON_PATH)

# --------------------------------------------------
# Generate ONE common sample dataset
# --------------------------------------------------

samples, s2_count, s1_count = build_training_samples(
    roi=roi,
    start_date="2021-03-01",
    end_date="2021-06-01",
    samples_per_class=1000,
)

# --------------------------------------------------
# Assign ONE common spatial split
# --------------------------------------------------

samples = assign_spatial_blocks(
    samples,
    block_size_m=1000,
)

blocks = (
    samples
    .distinct(["block_id"])
    .randomColumn(
        columnName="block_random",
        seed=42,
        rowKeys=["block_id"],
    )
)

joined = ee.Join.saveFirst(
    "matched_block"
).apply(
    primary=samples,
    secondary=blocks,
    condition=ee.Filter.equals(
        leftField="block_id",
        rightField="block_id",
    ),
)


def add_block_split(feature):

    feature = ee.Feature(feature)

    matched_block = ee.Feature(
        feature.get("matched_block")
    )

    return feature.set(
        "block_split",
        matched_block.get("block_random"),
    )


samples = ee.FeatureCollection(
    joined
).map(add_block_split)

training = samples.filter(
    ee.Filter.lt("block_split", 0.8)
)

validation = samples.filter(
    ee.Filter.gte("block_split", 0.8)
)


def evaluate_model(name, input_bands):

    classifier = (
        ee.Classifier.smileRandomForest(
            numberOfTrees=100,
            seed=42,
        )
        .train(
            features=training,
            classProperty="landcover",
            inputProperties=input_bands,
        )
    )

    predictions = validation.classify(
        classifier
    )

    matrix = predictions.errorMatrix(
        actual="landcover",
        predicted="classification",
        order=[1, 2, 3, 4],
    )

    print("\n" + "=" * 50)
    print(name)
    print("=" * 50)

    for row in matrix.array().getInfo():
        print(row)

    print(
        "Overall accuracy:",
        matrix.accuracy().getInfo(),
    )

    print(
        "Kappa:",
        matrix.kappa().getInfo(),
    )

    importance = classifier.explain().getInfo().get(
        "importance",
        {},
    )

    importance = dict(
        sorted(
            importance.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )

    print("\nVariable importance:")

    for variable, value in importance.items():
        print(f"{variable}: {value:.2f}")


print("Sentinel-2 scenes:", s2_count)
print("Sentinel-1 scenes:", s1_count)

print(
    "Training samples:",
    training.size().getInfo(),
)

print(
    "Validation samples:",
    validation.size().getInfo(),
)

print(
    "Training by class:",
    training.aggregate_histogram(
        "landcover"
    ).getInfo(),
)

print(
    "Validation by class:",
    validation.aggregate_histogram(
        "landcover"
    ).getInfo(),
)

# EXACTLY the same samples and spatial split.
evaluate_model(
    "MODEL A - 12 VARIABLES (NO SENTINEL-1)",
    BASE_INPUT_BANDS,
)

evaluate_model(
    "MODEL B - 14 VARIABLES (WITH SENTINEL-1)",
    INPUT_BANDS,
)