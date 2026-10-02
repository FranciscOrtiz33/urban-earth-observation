import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import folium
from streamlit_folium import st_folium

import ee
import streamlit as st

import hashlib

from src.exports import export_lst_to_drive

from src.city_search import (
    search_mexican_city,
    create_city_study_area,
)

# Make the project root importable when running from Streamlit.
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.lst import build_lst_composite, get_lst_statistics
from src.study_area import load_study_area


PROJECT_ID = "elite-variety-436219-b6"


st.set_page_config(
    page_title="Urban Earth Observation",
    page_icon="🛰️",
    layout="wide",
)

st.title("Urban Earth Observation")

st.write(
    "Land Surface Temperature analysis using "
    "Landsat 8/9 and Google Earth Engine."
)

st.subheader("1. Select a study area")

area_mode = st.radio(
    "Study area method",
    options=["Upload GeoJSON", "Search city"],
    horizontal=True,
)

uploaded_file = None
selected_city = None
radius_km = None

if area_mode == "Upload GeoJSON":

    uploaded_file = st.file_uploader(
        "Upload a GeoJSON containing your study area",
        type=["geojson", "json"],
    )

    st.caption(
        "The GeoJSON must contain Polygon or MultiPolygon "
        "geometries in EPSG:4326."
    )

else:

    city_name = st.text_input(
        "City",
        placeholder="Hermosillo",
    )

    state_name = st.text_input(
        "State",
        placeholder="Sonora",
    )

    radius_km = st.slider(
        "Study radius (km)",
        min_value=2,
        max_value=50,
        value=15,
        step=1,
    )

    query_key = (
        city_name.strip().casefold(),
        state_name.strip().casefold(),
    )

    if st.button("Search city"):

        if not city_name.strip() or not state_name.strip():

            st.warning("Enter a city and a state.")

        else:

            try:

                with st.spinner("Searching for the city..."):

                    place = search_mexican_city(
                        city_name=city_name.strip(),
                        state_name=state_name.strip(),
                    )

                st.session_state["city_search_result"] = {
                    "query_key": query_key,
                    "place": place,
                }

            except Exception as error:

                st.session_state.pop(
                    "city_search_result",
                    None,
                )

                st.error(f"City search failed: {error}")

    search_result = st.session_state.get(
        "city_search_result"
    )

    if (
        search_result is not None
        and search_result["query_key"] == query_key
    ):

        selected_city = search_result["place"]

        st.success("Location found!")

        st.write(selected_city["name"])

        st.write(
            f"Latitude: {selected_city['latitude']:.5f}"
        )

        st.write(
            f"Longitude: {selected_city['longitude']:.5f}"
        )

        st.caption(
            "The study area will be a circle around "
            "this location, not an official urban boundary."
        )

    else:

        st.info(
            "Enter a city and state, then click Search city."
        )

st.subheader("2. Select the study period")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "Start date",
        value=date(2025, 3, 1),
    )

with col2:
    end_date = st.date_input(
        "End date (inclusive)",
        value=date(2025, 5, 31),
    )


def load_uploaded_area(uploaded_file):
    """
    Temporarily save an uploaded GeoJSON and load its geometry.
    """

    with tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".geojson",
        delete=False,
    ) as temp_file:

        temp_file.write(uploaded_file.getvalue())
        temp_path = Path(temp_file.name)

    try:
        return load_study_area(temp_path)

    finally:
        temp_path.unlink(missing_ok=True)


def get_input_signature():
    """
    Identify the currently selected area and period.
    """

    dates = (
        start_date.isoformat(),
        end_date.isoformat(),
    )

    if area_mode == "Upload GeoJSON":

        if uploaded_file is None:
            return None

        file_hash = hashlib.sha256(
            uploaded_file.getvalue()
        ).hexdigest()

        return (
            "geojson",
            file_hash,
            *dates,
        )

    if selected_city is None:
        return None

    return (
        "city",
        selected_city["name"],
        selected_city["latitude"],
        selected_city["longitude"],
        radius_km,
        *dates,
    )

st.subheader("3. Run the analysis")

if st.button("Calculate LST", type="primary"):

    input_signature = get_input_signature()

    if input_signature is None:

        st.warning(
            "Select a GeoJSON or search for a city first."
        )

    elif end_date < start_date:

        st.error(
            "The end date cannot be before the start date."
        )

    else:

        # Clear the previous result before a new calculation.
        st.session_state.pop("lst_result", None)

        try:

            with st.spinner("Processing Landsat imagery..."):

                ee.Initialize(project=PROJECT_ID)

                if area_mode == "Upload GeoJSON":

                    roi = load_uploaded_area(uploaded_file)

                else:

                    roi = create_city_study_area(
                        latitude=selected_city["latitude"],
                        longitude=selected_city["longitude"],
                        radius_km=radius_km,
                    )

                end_date_exclusive = end_date + timedelta(days=1)

                lst_image, scene_count = build_lst_composite(
                    roi=roi,
                    start_date=start_date.isoformat(),
                    end_date=end_date_exclusive.isoformat(),
                )

                stats = get_lst_statistics(
                    lst_image=lst_image,
                    roi=roi,
                )

                st.session_state["lst_result"] = {
                    "image": lst_image,
                    "roi": roi,
                    "scene_count": scene_count,
                    "stats": stats,
                    "input_signature": input_signature,
                }

            st.success("Analysis saved successfully!")

        except Exception as error:

            st.exception(error)

# --------------------------------------------------
# Display a previously completed analysis
# --------------------------------------------------

result = st.session_state.get("lst_result")

if result is not None:

    # Check whether the selected area or dates changed.
    current_signature = get_input_signature()

    if current_signature != result["input_signature"]:

        st.info(
            "The study area or dates have changed. "
            "Click Calculate LST to update the results."
        )

    else:

        lst_image = result["image"]
        roi = result["roi"]
        scene_count = result["scene_count"]
        stats = result["stats"]

        st.success("LST analysis completed successfully!")

        st.write(f"**Landsat scenes found:** {scene_count}")

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "Mean LST",
            f"{stats['mean_c']:.2f} °C",
        )

        metric2.metric(
            "Minimum LST",
            f"{stats['min_c']:.2f} °C",
        )

        metric3.metric(
            "Maximum LST",
            f"{stats['max_c']:.2f} °C",
        )

        st.write(
            f"**Median LST:** {stats['median_c']:.2f} °C"
        )

        st.write(
            f"**Valid pixels:** {stats['valid_pixels']:,}"
        )

        # ------------------------------------------
        # Interactive map
        # ------------------------------------------

        st.subheader("4. Land Surface Temperature Map")

        lst_vis = {
            "min": 20,
            "max": 50,
            "palette": [
                "blue",
                "cyan",
                "green",
                "yellow",
                "orange",
                "red",
            ],
        }

        bounds = roi.bounds().coordinates().getInfo()[0]

        longitudes = [point[0] for point in bounds]
        latitudes = [point[1] for point in bounds]

        south = min(latitudes)
        north = max(latitudes)
        west = min(longitudes)
        east = max(longitudes)

        m = folium.Map(
            tiles=None,
            control_scale=True,
        )

        folium.TileLayer(
            tiles=(
                "https://server.arcgisonline.com/ArcGIS/rest/services/"
                "World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ),
            attr="Tiles © Esri",
            name="Esri World Imagery",
            overlay=False,
            control=True,
        ).add_to(m)

        lst_map_id = lst_image.getMapId(lst_vis)

        folium.TileLayer(
            tiles=lst_map_id["tile_fetcher"].url_format,
            attr="Map data © Google Earth Engine / USGS",
            name="Land Surface Temperature (°C)",
            overlay=True,
            control=True,
            opacity=0.85,
        ).add_to(m)

        folium.GeoJson(
            roi.getInfo(),
            name="Study Area",
            style_function=lambda feature: {
                "color": "white",
                "weight": 2,
                "fillOpacity": 0,
            },
        ).add_to(m)

        m.fit_bounds([
            [south, west],
            [north, east],
        ])

        folium.LayerControl().add_to(m)

        st_folium(
            m,
            height=600,
            returned_objects=[],
        )

        st.caption(
            "Median land surface temperature for the "
            "selected period. Values are in °C, "
            "not air temperature."
        )

        # ------------------------------------------
        # Export GeoTIFF
        # ------------------------------------------

        st.subheader("5. Export GeoTIFF")

        signature_id = hashlib.sha256(
            repr(result["input_signature"]).encode("utf-8")
        ).hexdigest()[:8]

        export_name = (
            f"LST_{start_date:%Y%m%d}"
            f"_{end_date:%Y%m%d}"
            f"_{signature_id}"
        )

        st.write(f"**Export name:** `{export_name}.tif`")

        current_export = st.session_state.get("lst_export")

        # Only associate an export with the inputs
        # that were used to create it.
        matching_export = (
            current_export is not None
            and current_export["input_signature"]
            == result["input_signature"]
        )

        export_running = (
            matching_export
            and current_export["status"]["state"]
            in {"READY", "RUNNING"}
        )

        if st.button(
            "Export LST to Google Drive",
            disabled=export_running,
        ):

            try:
                task = export_lst_to_drive(
                    lst_image=lst_image,
                    roi=roi,
                    export_name=export_name,
                )

                st.session_state["lst_export"] = {
                    "task": task,
                    "input_signature": result["input_signature"],
                    "status": task.status(),
                }

                st.success("Export task submitted!")

            except Exception as error:
                st.error(f"Export failed to start: {error}")

        # Show status across Streamlit reruns.
        current_export = st.session_state.get("lst_export")

        if (
            current_export is not None
            and current_export["input_signature"]
            == result["input_signature"]
        ):

            if st.button("Check export status"):

                try:
                    current_export["status"] = (
                        current_export["task"].status()
                    )

                except Exception as error:
                    st.error(
                        f"Could not check export status: {error}"
                    )

            status = current_export["status"]
            state = status["state"]

            st.write(f"**Export status:** {state}")

            if state == "COMPLETED":
                st.success(
                    "GeoTIFF export completed. "
                    "Check your Google Drive."
                )

            elif state == "FAILED":
                st.error(
                    status.get(
                        "error_message",
                        "The export task failed.",
                    )
                )

            elif state in {"READY", "RUNNING"}:
                st.info(
                    "Earth Engine is processing the export. "
                    "Click Check export status to refresh."
                )