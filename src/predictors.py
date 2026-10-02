import ee

from src.sentinel2 import build_sentinel2_composite


INPUT_BANDS = [
    "B2",
    "B3",
    "B4",
    "B8",
    "B11",
    "B12",
    "NDVI",
    "NDBI",
    "MNDWI",
    "BSI",
    "Elevation",
    "Slope",
]


def add_terrain_bands(image):
    """
    Add SRTM elevation and slope.

    SRTM has a native resolution of approximately 30 m.
    Bilinear resampling is used when evaluated on the
    10 m analysis grid.
    """

    dem = ee.Image("USGS/SRTMGL1_003").select("elevation")

    elevation = (
        dem
        .resample("bilinear")
        .rename("Elevation")
    )

    slope = (
        ee.Terrain.slope(dem)
        .resample("bilinear")
        .rename("Slope")
    )

    return image.addBands([
        elevation,
        slope,
    ])


def build_predictor_stack(
    roi,
    start_date,
    end_date,
):
    """
    Build the 12-band predictor stack used by
    the city-specific Random Forest.
    """

    sentinel2, scene_count = build_sentinel2_composite(
        roi=roi,
        start_date=start_date,
        end_date=end_date,
    )

    predictors = (
        add_terrain_bands(sentinel2)
        .select(INPUT_BANDS)
        .clip(roi)
    )

    return predictors, scene_count