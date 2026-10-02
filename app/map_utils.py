import folium


ESRI_WORLD_IMAGERY = (
    "https://server.arcgisonline.com/"
    "ArcGIS/rest/services/"
    "World_Imagery/MapServer/"
    "tile/{z}/{y}/{x}"
)


def _get_roi_bounds(roi):
    """
    Return Folium-compatible bounds for an Earth Engine geometry.
    """

    coordinates = (
        roi
        .bounds()
        .coordinates()
        .getInfo()[0]
    )

    longitudes = [
        point[0]
        for point in coordinates
    ]

    latitudes = [
        point[1]
        for point in coordinates
    ]

    return [
        [
            min(latitudes),
            min(longitudes),
        ],
        [
            max(latitudes),
            max(longitudes),
        ],
    ]


def _create_base_map(roi):
    """
    Create the common satellite basemap and ROI boundary.
    """

    map_object = folium.Map(
        tiles=None,
        control_scale=True,
    )

    folium.TileLayer(
        tiles=ESRI_WORLD_IMAGERY,
        attr="Tiles © Esri",
        name="Satellite",
        overlay=False,
    ).add_to(map_object)

    folium.GeoJson(
        roi.getInfo(),
        name="Study Area",
        style_function=lambda feature: {
            "color": "white",
            "weight": 2,
            "fillOpacity": 0,
        },
    ).add_to(map_object)

    map_object.fit_bounds(
        _get_roi_bounds(roi)
    )

    return map_object


def create_landcover_map(
    classified_image,
    roi,
    year,
    palette,
):
    """
    Create an interactive land-cover map.
    """

    visualization = {
        "min": 1,
        "max": 4,
        "palette": palette,
    }

    map_id = classified_image.getMapId(
        visualization
    )

    map_object = _create_base_map(
        roi
    )

    folium.TileLayer(
        tiles=(
            map_id[
                "tile_fetcher"
            ].url_format
        ),
        attr=(
            "Google Earth Engine / "
            "Copernicus / USGS / ESA"
        ),
        name=f"Land Cover {year}",
        overlay=True,
        opacity=0.75,
    ).add_to(map_object)

    folium.LayerControl().add_to(
        map_object
    )

    return map_object


def create_lst_map(
    lst_image,
    roi,
    year,
):
    """
    Create an interactive land-surface-temperature map.
    """

    visualization = {
        "min": 20,
        "max": 65,
        "palette": [
            "blue",
            "cyan",
            "green",
            "yellow",
            "orange",
            "red",
        ],
    }

    map_id = lst_image.getMapId(
        visualization
    )

    map_object = _create_base_map(
        roi
    )

    folium.TileLayer(
        tiles=(
            map_id[
                "tile_fetcher"
            ].url_format
        ),
        attr="Google Earth Engine / USGS",
        name=f"LST {year}",
        overlay=True,
        opacity=0.8,
    ).add_to(map_object)

    folium.LayerControl().add_to(
        map_object
    )

    return map_object