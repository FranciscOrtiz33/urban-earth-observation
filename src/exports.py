import ee
from src.config import ANALYSIS_SCALE

def export_lst_to_drive(
    lst_image,
    roi,
    export_name,
    folder="Urban_Earth_Observation",
):
    """
    Start a Google Earth Engine GeoTIFF export to Drive.

    Returns
    -------
    ee.batch.Task
        The started export task.
    """

    task = ee.batch.Export.image.toDrive(
        image=lst_image.toFloat(),
        description=export_name,
        folder=folder,
        fileNamePrefix=export_name,
        region=roi,
        scale=ANALYSIS_SCALE,
        maxPixels=1e13,
        fileFormat="GeoTIFF",
    )

    task.start()

    return task

def export_landcover_to_drive(
    classified_image,
    roi,
    start_date,
    end_date,
    export_name,
    folder="Urban_Earth_Observation",
):
    """
    Export a categorical land cover map aligned
    to a native 10 m Sentinel-2 B2 grid.

    Class values:
        0 = NoData
        1 = Vegetation
        2 = Built-up
        3 = Bare soil / sparse vegetation
        4 = Water
    """

    reference_collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(
            ee.Filter.lt(
                "CLOUDY_PIXEL_PERCENTAGE",
                30,
            )
        )
    )

    reference_image = ee.Image(
        reference_collection.first()
    )

    reference_grid = (
        reference_image
        .select("B2")
        .projection()
        .getInfo()
    )

    export_image = (
        classified_image
        .unmask(
            value=0,
            sameFootprint=False,
        )
        .toByte()
    )

    task = ee.batch.Export.image.toDrive(
        image=export_image,
        description=export_name,
        folder=folder,
        fileNamePrefix=export_name,
        region=roi,
        crs=reference_grid["crs"],
        crsTransform=reference_grid["transform"],
        maxPixels=1e13,
        fileFormat="GeoTIFF",
        formatOptions={
            "noData": 0,
        },
    )

    task.start()

    return task, reference_grid