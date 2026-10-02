import json

import ee


def load_study_area(file_path):
    """
    Load a Polygon or MultiPolygon study area from GeoJSON.

    Supports Geometry, Feature and FeatureCollection.
    The input GeoJSON must use EPSG:4326 coordinates.
    """

    with open(file_path, "r", encoding="utf-8-sig") as file:
        geojson_data = json.load(file)

    geojson_type = geojson_data.get("type")

    if geojson_type == "FeatureCollection":
        features = geojson_data.get("features", [])

        if not features:
            raise ValueError("The GeoJSON contains no features.")

        geometries = [
            feature.get("geometry")
            for feature in features
        ]

    elif geojson_type == "Feature":
        geometries = [geojson_data.get("geometry")]

    else:
        geometries = [geojson_data]

    for geometry in geometries:
        if not isinstance(geometry, dict):
            raise ValueError("A feature has no geometry.")

        if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(
                "The study area must contain "
                "Polygon or MultiPolygon geometries."
            )

    ee_geometries = [
        ee.Geometry(geometry)
        for geometry in geometries
    ]

    if len(ee_geometries) == 1:
        return ee_geometries[0]

    return ee.FeatureCollection(
        [ee.Feature(geometry) for geometry in ee_geometries]
    ).geometry()