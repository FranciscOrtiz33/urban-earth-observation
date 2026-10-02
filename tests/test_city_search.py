from src.city_search import search_mexican_city


city = search_mexican_city(
    city_name="Hermosillo",
    state_name="Sonora",
)

print("Place:", city["name"])
print("Latitude:", city["latitude"])
print("Longitude:", city["longitude"])