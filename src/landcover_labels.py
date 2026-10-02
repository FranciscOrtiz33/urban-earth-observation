import ee


CLASS_NAMES = {
    1: "Vegetation",
    2: "Built-up",
    3: "Bare soil / sparse vegetation",
    4: "Water",
}


def get_worldcover_labels(roi):
    """
    Reclassify ESA WorldCover 2021 into
    the four project classes.
    """

    worldcover = (
        ee.ImageCollection(
            "ESA/WorldCover/v200"
        )
        .filterBounds(roi)
        .mosaic()
        .select("Map")
        .clip(roi)
    )

    labels = worldcover.remap(
        [
            10,
            20,
            30,
            40,
            50,
            60,
            80,
            90,
            95,
            100,
        ],
        [
            1,
            1,
            1,
            1,
            2,
            3,
            4,
            1,
            1,
            1,
        ],
    )

    return (
        labels
        .rename("landcover")
        .toByte()
        .clip(roi)
    )