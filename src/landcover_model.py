import ee

from src.config import RF_TREES, RANDOM_SEED
from src.predictors import INPUT_BANDS


CLASS_VALUES = [1, 2, 3, 4]


def train_city_model(samples):
    """
    Train one Random Forest for one city.

    80% training / 20% test.
    """

    training = samples.filter(
        ee.Filter.lt(
            "random",
            0.8,
        )
    )

    test = samples.filter(
        ee.Filter.gte(
            "random",
            0.8,
        )
    )

    classifier = (
        ee.Classifier.smileRandomForest(
            numberOfTrees=RF_TREES,
            seed=RANDOM_SEED,
        )
        .train(
            features=training,
            classProperty="landcover",
            inputProperties=INPUT_BANDS,
        )
    )

    predictions = test.classify(
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
        test,
        confusion_matrix,
    )