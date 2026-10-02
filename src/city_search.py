import ee

from geopy.geocoders import Nominatim


geolocator = Nominatim(
    user_agent="urban-earth-observation-local/0.1",
    timeout=10,
)


def search_mexican_city(city_name, state_name):
    """
    Find a location in Mexico by city and state name.

    Returns
    -------
    dict
        Place name and coordinates.
    """

    query = f"{city_name}, {state_name}, México"

    location = geolocator.geocode(
        query,
        country_codes="mx",
        exactly_one=True,
        language="es",
    )

    if location is None:
        raise ValueError(
            "City not found. Check the city and state names."
        )

    return {
        "name": location.address,
        "latitude": location.latitude,
        "longitude": location.longitude,
    }


def create_city_study_area(latitude, longitude, radius_km):
    """
    Create a circular study area around a location.
    """

    if radius_km <= 0:
        raise ValueError("Radius must be greater than zero.")

    point = ee.Geometry.Point([
        longitude,
        latitude,
    ])

    return point.buffer(radius_km * 1000)