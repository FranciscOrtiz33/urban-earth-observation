import ee


SAR_BANDS = [
    "VV",
    "VH",
]


def build_sentinel1_composite(
    roi,
    start_date,
    end_date,
):
    """
    Build a Sentinel-1 median SAR composite
    using VV and VH polarization.

    Output values are in decibels (dB).
    """

    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(
            ee.Filter.eq(
                "instrumentMode",
                "IW",
            )
        )
        .filter(
            ee.Filter.eq(
                "resolution_meters",
                10,
            )
        )
        .filter(
            ee.Filter.listContains(
                "transmitterReceiverPolarisation",
                "VV",
            )
        )
        .filter(
            ee.Filter.listContains(
                "transmitterReceiverPolarisation",
                "VH",
            )
        )
        .select(SAR_BANDS)
    )

    scene_count = collection.size().getInfo()

    if scene_count == 0:
        raise ValueError(
            "No Sentinel-1 VV/VH images were found "
            "for the selected area and period."
        )

    composite = (
        collection
        .median()
        .rename([
            "S1_VV",
            "S1_VH",
        ])
        .clip(roi)
    )

    return composite, scene_count