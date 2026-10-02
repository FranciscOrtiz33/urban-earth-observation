import ee

from src.config import MAX_CLOUD_PERCENTAGE


SPECTRAL_BANDS = [
    "B2",
    "B3",
    "B4",
    "B8",
    "B11",
    "B12",
]


def mask_s2_qa60(image):
    """
    Thesis-style QA60 cloud mask.
    """

    qa = image.select("QA60")

    cloud_bit = 1 << 10
    cirrus_bit = 1 << 11

    mask = (
        qa.bitwiseAnd(cloud_bit).eq(0)
        .And(
            qa.bitwiseAnd(cirrus_bit).eq(0)
        )
    )

    return (
        image
        .updateMask(mask)
        .select(SPECTRAL_BANDS)
        .resample("bilinear")
        .divide(10000)
        .copyProperties(
            image,
            ["system:time_start"],
        )
    )


def mask_s2_scl(image):
    """
    Fallback cloud mask for the QA60 gap.
    """

    scl = image.select("SCL")

    mask = (
        scl.neq(0)
        .And(scl.neq(1))
        .And(scl.neq(3))
        .And(scl.neq(8))
        .And(scl.neq(9))
        .And(scl.neq(10))
        .And(scl.neq(11))
    )

    return (
        image
        .updateMask(mask)
        .select(SPECTRAL_BANDS)
        .resample("bilinear")
        .divide(10000)
        .copyProperties(
            image,
            ["system:time_start"],
        )
    )


def add_spectral_indices(image):

    ndvi = image.normalizedDifference(
        ["B8", "B4"]
    ).rename("NDVI")

    ndbi = image.normalizedDifference(
        ["B11", "B8"]
    ).rename("NDBI")

    mndwi = image.normalizedDifference(
        ["B3", "B11"]
    ).rename("MNDWI")

    bsi = image.expression(
        "((SWIR + RED) - (NIR + BLUE)) / "
        "((SWIR + RED) + (NIR + BLUE))",
        {
            "SWIR": image.select("B11"),
            "RED": image.select("B4"),
            "NIR": image.select("B8"),
            "BLUE": image.select("B2"),
        },
    ).rename("BSI")

    return image.addBands([
        ndvi,
        ndbi,
        mndwi,
        bsi,
    ])


def build_sentinel2_composite(
    roi,
    start_date,
    end_date,
):
    """
    Build the Sentinel-2 composite used by the model.
    """

    collection = (
        ee.ImageCollection(
            "COPERNICUS/S2_SR_HARMONIZED"
        )
        .filterBounds(roi)
        .filterDate(
            start_date,
            end_date,
        )
        .filter(
            ee.Filter.lt(
                "CLOUDY_PIXEL_PERCENTAGE",
                MAX_CLOUD_PERCENTAGE,
            )
        )
    )

    scene_count = collection.size().getInfo()

    if scene_count == 0:
        raise ValueError(
            "No Sentinel-2 images were found "
            "for the selected area and period."
        )

    year = int(start_date[:4])

    # QA60 was unavailable during most of
    # 2022-2023 and early 2024.
    if year in {2022, 2023}:
        mask_function = mask_s2_scl
    else:
        mask_function = mask_s2_qa60

    composite = (
        collection
        .map(mask_function)
        .map(add_spectral_indices)
        .median()
        .clip(roi)
    )

    return composite, scene_count