import ee

from src.predictors import INPUT_BANDS


CLASS_VALUES = [1, 2, 3, 4]


def assign_spatial_blocks(samples, block_size_m=1000):
    """
    Assign each sample to a spatial block.

    Blocks use EPSG:3857 projected coordinates.
    The block size is approximate in ground distance.
    """

    projection = ee.Projection("EPSG:3857")

    def add_block_id(feature):

        coordinates = (
            feature.geometry()
            .transform(projection, 1)
            .coordinates()
        )

        x = (
            ee.Number(coordinates.get(0))
            .divide(block_size_m)
            .floor()
        )

        y = (
            ee.Number(coordinates.get(1))
            .divide(block_size_m)
            .floor()
        )

        block_id = (
            x.format("%d")
            .cat("_")
            .cat(y.format("%d"))
        )

        return feature.set(
            "block_id",
            block_id,
        )

    return samples.map(add_block_id)


def train_with_spatial_validation(
    samples,
    block_size_m=1000,
    number_of_trees=100,
    input_bands=None,
):
    """
    Train and evaluate Random Forest using
    spatially separated blocks.
    """

    if input_bands is None:
        input_bands = INPUT_BANDS

    samples = assign_spatial_blocks(
        samples,
        block_size_m=block_size_m,
    )

    # Give each unique block one random split value.
    blocks = (
        samples
        .distinct(["block_id"])
        .randomColumn(
            columnName="block_random",
            seed=42,
            rowKeys=["block_id"],
        )
    )

    # Attach the block split to every sample.
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

    classifier = (
        ee.Classifier.smileRandomForest(
            numberOfTrees=number_of_trees,
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

    confusion_matrix = predictions.errorMatrix(
        actual="landcover",
        predicted="classification",
        order=CLASS_VALUES,
    )

    return (
        classifier,
        training,
        validation,
        confusion_matrix,
    )