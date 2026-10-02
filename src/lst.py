import ee
from src.config import ANALYSIS_SCALE


def get_landsat_collection(roi, start_date, end_date):
    """
    Retrieve Landsat 8 and 9 images with surface temperature data.

    The end date is exclusive.
    """

    landsat8 = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("PROCESSING_LEVEL", "L2SP"))
    )

    landsat9 = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("PROCESSING_LEVEL", "L2SP"))
    )

    landsat = landsat8.merge(landsat9)

    return landsat8, landsat9, landsat


def calculate_lst(image):
    """
    Convert one Landsat image to surface temperature in Celsius.
    """

    qa = image.select("QA_PIXEL")

    # Exclude fill, dilated clouds, cirrus, clouds,
    # cloud shadows and snow.
    clear_mask = qa.bitwiseAnd(0b111111).eq(0)

    lst = (
        image.select("ST_B10")
        .multiply(0.00341802)
        .add(149.0)
        .subtract(273.15)
        .rename("LST_C")
    )

    return (
        lst
        .updateMask(clear_mask)
        .copyProperties(image, ["system:time_start"])
    )


def build_lst_composite(roi, start_date, end_date):
    """
    Build a median LST composite for an area and date range.

    Returns
    -------
    tuple
        (lst_composite, scene_count)
    """

    _, _, landsat = get_landsat_collection(
        roi=roi,
        start_date=start_date,
        end_date=end_date,
    )

    scene_count = landsat.size().getInfo()

    if scene_count == 0:
        raise ValueError(
            "No Landsat images were found "
            "for the selected area and period."
        )

    lst_collection = landsat.map(calculate_lst)

    lst_composite = (
        lst_collection
        .median()
        .clip(roi)
    )

    return lst_composite, scene_count


def get_lst_statistics(lst_image, roi):
    """
    Calculate spatial statistics for an LST composite.
    """

    reducer = (
        ee.Reducer.mean()
        .combine(
            reducer2=ee.Reducer.minMax(),
            sharedInputs=True,
        )
        .combine(
            reducer2=ee.Reducer.percentile(
                [2, 25, 50, 75, 98]
            ),
            sharedInputs=True,
        )
        .combine(
            reducer2=ee.Reducer.count(),
            sharedInputs=True,
        )
    )

    results = lst_image.reduceRegion(
        reducer=reducer,
        geometry=roi,
        scale=ANALYSIS_SCALE,
        maxPixels=1e10,
        tileScale=4,
    ).getInfo()

    if not results or results.get("LST_C_count", 0) == 0:
        raise ValueError(
            "No valid LST pixels were found "
            "for the selected area and period."
        )

    return {
        "mean_c": results["LST_C_mean"],
        "min_c": results["LST_C_min"],
        "max_c": results["LST_C_max"],
        "p2_c": results["LST_C_p2"],
        "p25_c": results["LST_C_p25"],
        "median_c": results["LST_C_p50"],
        "p75_c": results["LST_C_p75"],
        "p98_c": results["LST_C_p98"],
        "valid_pixels": results["LST_C_count"],
    }