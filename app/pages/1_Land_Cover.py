import sys


from datetime import date


from pathlib import Path


import matplotlib.pyplot as plt


from src.exports import export_landcover_to_drive


from src.thermal_landcover import (


    analyze_year_temperature_by_class,


    analyze_multiyear_temperature_by_class,


)


import streamlit as st


from streamlit_folium import st_folium


# --------------------------------------------------


# Project imports


# --------------------------------------------------


PROJECT_ROOT = Path(__file__).resolve().parents[2]


sys.path.insert(0, str(PROJECT_ROOT))


from app.map_utils import (
    create_landcover_map,
    create_lst_map,
)

from app.analysis_controller import (
    get_area_signature,
    initialize_analysis_state,
    run_landcover_analysis,
)

from app.table_utils import (
    build_area_dataframe,
    build_confusion_dataframe,
    build_gains_losses_dataframe,
    build_integrated_change_dataframe,
    build_integrated_summary,
    build_landsat_metadata_dataframe,
    build_multiyear_thermal_dataframe,
    build_net_change_dataframe,
    build_sentinel_metadata_dataframe,
    build_temperature_difference_dataframe,
    build_thermal_statistics_dataframe,
    build_transition_dataframe,
)


from src.city_search import (
    search_mexican_city,
)
PROJECT_ID = "elite-variety-436219-b6"


CLASS_NAMES = [


    "Vegetation",


    "Built-up",


    "Bare soil / sparse vegetation",


    "Water",


]


CLASS_PALETTE = [


    "228B22",  # Vegetation


    "FF0000",  # Built-up


    "F2D16B",  # Bare soil


    "0066FF",  # Water


]


# --------------------------------------------------


# Page


# --------------------------------------------------


st.set_page_config(


    page_title="Land Cover Analysis",


    page_icon="🛰️",


    layout="wide",


)


st.title("Land Cover Classification")


st.write(


    "City-specific land-cover classification using "


    "Sentinel-2, SRTM, ESA WorldCover and Random Forest."


)


st.caption(


    "A Random Forest model is trained for each study area "


    "using 2021 data and reused for inference in the "


    "selected years."


)


# --------------------------------------------------
# 1. Study area


# --------------------------------------------------


st.subheader("1. Select study area")


area_mode = st.radio(


    "Study area method",


    [


        "Search city",


        "Upload GeoJSON",


    ],


    horizontal=True,


)


uploaded_file = None


selected_city = None


radius_km = None


if area_mode == "Search city":


    col1, col2 = st.columns(2)


    with col1:


        city_name = st.text_input(


            "City",


            placeholder="Guadalajara",


        )


    with col2:


        state_name = st.text_input(


            "State",


            placeholder="Jalisco",


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


    if st.button(


        "Search city",


        key="lc_search_city",


    ):


        if (


            not city_name.strip()


            or not state_name.strip()


        ):


            st.warning(


                "Enter a city and state."


            )


        else:


            try:


                with st.spinner(


                    "Searching city..."


                ):


                    place = (


                        search_mexican_city(


                            city_name.strip(),


                            state_name.strip(),


                        )


                    )


                st.session_state[


                    "lc_city_search"


                ] = {


                    "query_key": query_key,


                    "place": place,


                }


            except Exception as error:


                st.error(


                    f"City search failed: {error}"


                )


    search_result = (


        st.session_state.get(


            "lc_city_search"


        )


    )


    if (


        search_result is not None


        and search_result["query_key"]


        == query_key


    ):


        selected_city = (


            search_result["place"]


        )


        st.success(


            "Location found."


        )


        st.write(


            selected_city["name"]


        )


        st.caption(


            "The ROI is a circular study area "


            "around the selected location."


        )


else:


    uploaded_file = st.file_uploader(


        "Upload study area",


        type=[


            "geojson",


            "json",


        ],


        key="lc_geojson",


    )


    st.caption(


        "Polygon or MultiPolygon in EPSG:4326."


    )


# --------------------------------------------------


# 2. Years


# --------------------------------------------------


st.subheader("2. Select years")


current_year = date.today().year


available_years = list(


    range(


        2018,


        current_year + 1,


    )


)


default_years = [


    year


    for year in [


        2018,


        2021,


        2025,


    ]


    if year in available_years


]


selected_years = st.multiselect(


    "Years to classify",


    options=available_years,


    default=default_years,


)


st.caption(


    "The 2021 reference year is always included "


    "internally because it is used to train the "


    "city-specific model."


)


# --------------------------------------------------
# 3. Run
# --------------------------------------------------

st.subheader(
    "3. Run land-cover analysis"
)

area_signature = get_area_signature(
    area_mode=area_mode,
    uploaded_file=uploaded_file,
    selected_city=selected_city,
    radius_km=radius_km,
)

initialize_analysis_state(
    st.session_state
)

if st.button(
    "Run Land Cover Analysis",
    type="primary",
):
    if area_signature is None:
        st.warning(
            "Select a study area first."
        )

    elif not selected_years:
        st.warning(
            "Select at least one year."
        )

    else:
        try:
            model_was_cached = (
                area_signature
                in st.session_state[
                    "landcover_models"
                ]
            )

            if model_was_cached:
                spinner_message = (
                    "Classifying selected years "
                    "with the existing 2021 model..."
                )
            else:
                spinner_message = (
                    "Training the 2021 city model "
                    "and classifying selected years..."
                )

            with st.spinner(
                spinner_message
            ):
                (
                    _,
                    model_reused,
                ) = run_landcover_analysis(
                    session_state=
                        st.session_state,
                    project_id=
                        PROJECT_ID,
                    area_signature=
                        area_signature,
                    area_mode=
                        area_mode,
                    uploaded_file=
                        uploaded_file,
                    selected_city=
                        selected_city,
                    radius_km=
                        radius_km,
                    selected_years=
                        selected_years,
                )

            if model_reused:
                st.info(
                    "Using the 2021 model already "
                    "trained for this study area."
                )

        except Exception as error:
            st.exception(
                error
            )


# --------------------------------------------------
# Display stored results


# --------------------------------------------------


result = st.session_state.get(


    "landcover_result"


)


if result is not None:


    current_signature = (


        area_signature,


        tuple(


            sorted(


                selected_years


            )


        ),


    )


    if (


        current_signature


        != result["signature"]


    ):


        st.info(


            "The study area or selected years "


            "changed. Run the analysis again."


        )


    else:


        # ------------------------------------------


        # Model performance


        # ------------------------------------------


        st.subheader(


            "4. 2021 model performance"


        )


        metrics = result["metrics"]


        c1, c2, c3, c4 = st.columns(4)


        c1.metric(


            "Accuracy",


            f"{metrics['accuracy'] * 100:.2f}%",


        )


        c2.metric(


            "Kappa",


            f"{metrics['kappa']:.4f}",


        )


        c3.metric(


            "Training samples",


            f"{metrics['training_samples']:,}",


        )


        c4.metric(


            "Test samples",


            f"{metrics['test_samples']:,}",


        )


        confusion_df = build_confusion_dataframe(
            metrics=metrics,
            class_names=CLASS_NAMES,
        )

        st.write(


            "**Confusion matrix**"


        )


        st.dataframe(


            confusion_df,


            use_container_width=True,


        )


        # ------------------------------------------


        # Areas


        # ------------------------------------------


        st.subheader(


            "5. Land-cover areas"


        )


        areas_df = build_area_dataframe(
            result["areas"]
        )

        st.dataframe(


            areas_df,


            use_container_width=True,


        )


        st.write("**Satellite observations used**")


        metadata_df = build_sentinel_metadata_dataframe(
            result["metadata"]
        )

        st.dataframe(


            metadata_df,


            use_container_width=True,


        )


        # ------------------------------------------


        # Map


        # ------------------------------------------


        st.subheader(


            "6. Classified map"


        )


        years_available = sorted(


            result["maps"].keys()


        )


        map_year = st.selectbox(


            "Year to display",


            years_available,


        )


        classified_image = (


            result["maps"][


                map_year


            ]


        )


        classified_map = create_landcover_map(
            classified_image=classified_image,
            roi=result["roi"],
            year=map_year,
            palette=CLASS_PALETTE,
        )

        st_folium(
            classified_map,
            height=650,
            returned_objects=[],
            key=f"landcover_map_{map_year}",
        )


        st.subheader("7. Land-cover trends")


        trend_df = areas_df.copy()


        st.line_chart(


            trend_df,


            use_container_width=True,


        )


        st.write("**Land-cover comparison by year**")


        st.bar_chart(


            trend_df,


            use_container_width=True,


        )


        st.subheader("8. Net land-cover change")


        net_change_df = build_net_change_dataframe(
            net_changes=result["net_changes"],
            start_year=result["change_start"],
            end_year=result["change_end"],
        )

        st.dataframe(


            net_change_df.style.format({


                f"{result['change_start']} (ha)": "{:,.2f}",


                f"{result['change_end']} (ha)": "{:,.2f}",


                "Change (ha)": "{:+,.2f}",


                "Change (%)": "{:+.2f}%",


            }),


            use_container_width=True,


        )


        st.subheader("9. Gains and losses")


        gains_df = build_gains_losses_dataframe(
            result["gains_losses"]
        )

        st.dataframe(


            gains_df.style.format({


                "Stable (ha)": "{:,.2f}",


                "Gains (ha)": "{:,.2f}",


                "Losses (ha)": "{:,.2f}",


                "Net change (ha)": "{:+,.2f}",


            }),


            use_container_width=True,


        )


        st.subheader(


            "10. Land-cover transition matrix"


        )


        transition_df = build_transition_dataframe(
            transition_matrix=result["transition_matrix"],
            class_names=CLASS_NAMES,
            start_year=result["transition_start"],
            end_year=result["transition_end"],
        )

        st.dataframe(


            transition_df.style.format(


                "{:,.2f}"


            ),


            use_container_width=True,


        )


        st.write("**Transition heatmap**")


        fig, ax = plt.subplots(


            figsize=(8, 6)


        )


        matrix_values = (


            transition_df.values


        )


        image = ax.imshow(


            matrix_values


        )


        fig.colorbar(


            image,


            ax=ax,


            label="Area (ha)",


        )


        ax.set_xticks(


            range(len(CLASS_NAMES))


        )


        ax.set_xticklabels(


            CLASS_NAMES,


            rotation=45,


            ha="right",


        )


        ax.set_yticks(


            range(len(CLASS_NAMES))


        )


        ax.set_yticklabels(


            CLASS_NAMES,


        )


        for i in range(


            matrix_values.shape[0]


        ):


            for j in range(


                matrix_values.shape[1]


            ):


                ax.text(


                    j,


                    i,


                    f"{matrix_values[i, j]:,.0f}",


                    ha="center",


                    va="center",


                )


        ax.set_xlabel(


            f"Final class ({result['transition_end']})"


        )


        ax.set_ylabel(


            f"Initial class ({result['transition_start']})"


        )


        ax.set_title(


            "Land-cover transition matrix"


        )


        fig.tight_layout()


        st.pyplot(fig)


        plt.close(fig)


        st.subheader("11. Export classified GeoTIFF")


        export_year = st.selectbox(


            "Year to export",


            sorted(result["maps"].keys()),


            key="lc_export_year",


        )


        export_metadata = (


            result["metadata"][export_year]


        )


        export_image = (


            result["maps"][export_year]


        )


        export_name = (


            f"LandCover_{export_year}_"


            f"{area_signature[:8]}"


        )


        st.write(


            f"**File:** `{export_name}.tif`"


        )


        if "landcover_exports" not in st.session_state:


            st.session_state[


                "landcover_exports"


            ] = {}


        if st.button(


            "Export GeoTIFF to Google Drive",


            key="lc_export_button",


        ):


            try:


                task, grid = export_landcover_to_drive(


                    classified_image=export_image,


                    roi=result["roi"],


                    start_date=


                        export_metadata["start_date"],


                    end_date=


                        export_metadata["end_date"],


                    export_name=export_name,


                )


                st.session_state[


                    "landcover_exports"


                ][export_name] = {


                    "task": task,


                    "status": task.status(),


                    "grid": grid,


                }


                st.success(


                    "Export task submitted."


                )


            except Exception as error:


                st.exception(error)


        export_info = (


            st.session_state[


                "landcover_exports"


            ].get(export_name)


        )


        if export_info is not None:


            if st.button(


                "Check export status",


                key="lc_check_export",


            ):


                export_info["status"] = (


                    export_info[


                        "task"


                    ].status()


                )


            status = (


                export_info["status"]


            )


            st.write(


                f"**Status:** "


                f"{status['state']}"


            )


            if status["state"] == "COMPLETED":


                st.success(


                    "GeoTIFF completed. "


                    "Check Google Drive."


                )


            elif status["state"] == "FAILED":


                st.error(


                    status.get(


                        "error_message",


                        "Export failed.",


                    )


                )


        st.subheader(


            "12. Thermal behavior by land cover"


        )


        thermal_year = st.selectbox(


            "Year for thermal analysis",


            options=sorted(result["maps"].keys()),


            key="thermal_landcover_year",


        )


        thermal_key = (


            area_signature,


            thermal_year,


        )


        if st.button(


            "Analyze LST by land cover",


            key="thermal_landcover_button",


        ):


            try:


                with st.spinner(


                    f"Calculating surface temperature "


                    f"for {thermal_year}..."


                ):


                    thermal_result = (


                        analyze_year_temperature_by_class(


                            roi=result["roi"],


                            classified_image=


                                result["maps"][thermal_year],


                            year=thermal_year,


                        )


                    )


                    st.session_state[


                        "thermal_landcover_results"


                    ][thermal_key] = thermal_result


            except Exception as error:


                st.exception(error)


        thermal_result = (

            st.session_state

            .get("thermal_landcover_results", {})

            .get(thermal_key)

        )


        if thermal_result is None:

            st.info(

                "Click 'Analyze LST by land cover' to calculate "

                f"thermal statistics for {thermal_year}."

            )


        else:

            st.success(

                "Thermal analysis completed."

            )


            st.write(

                f"**Landsat scenes:** "

                f"{thermal_result['scene_count']}"

            )


            st.write(

                f"**Period:** "

                f"{thermal_result['start_date']} "

                f"to "

                f"{thermal_result['end_date']}"

            )


            # ------------------------------------------

            # Thermal statistics table

            # ------------------------------------------


            thermal_df = build_thermal_statistics_dataframe(
                thermal_result["statistics"]
            )

            if not thermal_df.empty:

                st.dataframe(

                    thermal_df.style.format({

                        "Mean LST (°C)": "{:.2f}",

                        "Median LST (°C)": "{:.2f}",

                        "Minimum LST (°C)": "{:.2f}",

                        "Maximum LST (°C)": "{:.2f}",

                        "Valid pixels": "{:,.0f}",

                    }),

                    use_container_width=True,

                )


                st.write(

                    "**Mean surface temperature by land cover**"

                )


                st.bar_chart(

                    thermal_df[["Mean LST (°C)"]],

                    use_container_width=True,

                )


            else:

                st.warning(

                    "No valid thermal statistics were found "

                    f"for {thermal_year}."

                )


            # ------------------------------------------

            # LST map

            # ------------------------------------------


            st.write(

                f"**Land Surface Temperature Map — "

                f"{thermal_year}**"

            )


            lst_image = thermal_result["lst_image"]

            thermal_map = create_lst_map(
                lst_image=lst_image,
                roi=result["roi"],
                year=thermal_year,
            )

            st_folium(
                thermal_map,
                height=650,
                returned_objects=[],
                key=f"thermal_map_{thermal_year}",
            )


            st.caption(

                "Surface temperature derived from Landsat 8/9. "

                "The map is evaluated on the project's 10 m "

                "working grid, but this does not imply native "

                "10 m thermal resolution."

            )


        # --------------------------------------------------
        # Multiyear thermal analysis
        # --------------------------------------------------

        st.subheader(
            "13. Multiyear thermal analysis"
        )

        st.write(
            "Compare land surface temperature by "
            "land-cover class across all analyzed years."
        )

        multiyear_thermal_key = (
            area_signature,
            tuple(
                sorted(
                    result["maps"].keys()
                )
            ),
        )

        if st.button(
            "Analyze thermal evolution",
            key="multiyear_thermal_button",
        ):
            try:
                with st.spinner(
                    "Calculating LST for all years..."
                ):
                    multiyear_thermal = (
                        analyze_multiyear_temperature_by_class(
                            roi=result["roi"],
                            classified_maps=result["maps"],
                        )
                    )

                    st.session_state[
                        "thermal_landcover_results"
                    ][multiyear_thermal_key] = (
                        multiyear_thermal
                    )

            except Exception as error:
                st.exception(error)

        multiyear_thermal = (
            st.session_state
            .get(
                "thermal_landcover_results",
                {},
            )
            .get(multiyear_thermal_key)
        )

        if multiyear_thermal is None:
            st.info(
                "Click 'Analyze thermal evolution' to compare "
                "LST across all analyzed years."
            )

        else:
            st.success(
                "Multiyear thermal analysis completed."
            )

            # ----------------------------------------------
            # Mean LST
            # ----------------------------------------------

            thermal_mean_df = build_multiyear_thermal_dataframe(
                multiyear_thermal=multiyear_thermal,
                class_names=CLASS_NAMES,
                statistic_key="mean_c",
            )

            st.write(
                "**Mean LST by land-cover class (°C)**"
            )

            st.dataframe(
                thermal_mean_df.style.format(
                    "{:.2f}"
                ),
                use_container_width=True,
            )

            st.line_chart(
                thermal_mean_df,
                use_container_width=True,
            )

            # ----------------------------------------------
            # Median LST
            # ----------------------------------------------

            thermal_median_df = build_multiyear_thermal_dataframe(
                multiyear_thermal=multiyear_thermal,
                class_names=CLASS_NAMES,
                statistic_key="median_c",
            )

            st.write(
                "**Median LST by land-cover class (°C)**"
            )

            st.dataframe(
                thermal_median_df.style.format(
                    "{:.2f}"
                ),
                use_container_width=True,
            )

            # ----------------------------------------------
            # Difference relative to vegetation
            # ----------------------------------------------

            thermal_difference_df = (
                build_temperature_difference_dataframe(
                    thermal_mean_df=thermal_mean_df,
                    reference_class="Vegetation",
                )
            )

            st.write(
                "**Temperature difference relative "
                "to vegetation (°C)**"
            )

            st.dataframe(
                thermal_difference_df.style.format(
                    "{:+.2f}"
                ),
                use_container_width=True,
            )

            st.bar_chart(
                thermal_difference_df,
                use_container_width=True,
            )

            # ----------------------------------------------
            # Landsat metadata
            # ----------------------------------------------

            thermal_metadata_df = build_landsat_metadata_dataframe(
                multiyear_thermal
            )

            st.write(
                "**Landsat observations used**"
            )

            st.dataframe(
                thermal_metadata_df,
                use_container_width=True,
            )

            st.caption(
                "LST is derived from Landsat 8/9. "
                "Values are evaluated on the project's "
                "10 m working grid; resampling does not "
                "create native 10 m thermal information."
            )

            # ----------------------------------------------
            # Integrated land-cover + thermal change
            # ----------------------------------------------

            st.subheader(
                "14. Integrated land-cover and thermal change"
            )

            (
                integrated_df,
                first_year,
                last_year,
            ) = build_integrated_change_dataframe(
                areas=result["areas"],
                thermal_mean_df=thermal_mean_df,
                class_names=CLASS_NAMES,
            )

            st.dataframe(
                integrated_df.style.format({
                    f"Area {first_year} (ha)":
                        "{:,.2f}",
                    f"Area {last_year} (ha)":
                        "{:,.2f}",
                    "Area change (ha)":
                        "{:+,.2f}",
                    f"Mean LST {first_year} (°C)":
                        "{:.2f}",
                    f"Mean LST {last_year} (°C)":
                        "{:.2f}",
                    "LST change (°C)":
                        "{:+.2f}",
                }),
                use_container_width=True,
            )

            # ----------------------------------------------
            # Summary indicators
            # ----------------------------------------------

            integrated_summary = build_integrated_summary(
                areas=result["areas"],
                thermal_mean_df=thermal_mean_df,
                first_year=first_year,
                last_year=last_year,
            )

            built_up_change = (
                integrated_summary[
                    "built_up_area_change"
                ]
            )

            vegetation_change = (
                integrated_summary[
                    "vegetation_area_change"
                ]
            )

            built_up_lst_change = (
                integrated_summary[
                    "built_up_lst_change"
                ]
            )

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Built-up area change",
                f"{built_up_change:+,.2f} ha",
            )

            c2.metric(
                "Vegetation area change",
                f"{vegetation_change:+,.2f} ha",
            )

            if built_up_lst_change is None:
                c3.metric(
                    "Built-up LST change",
                    "N/A",
                )
            else:
                c3.metric(
                    "Built-up LST change",
                    f"{built_up_lst_change:+.2f} °C",
                )

            st.caption(
                "Area change and thermal change describe "
                "different phenomena. A change in built-up "
                "area does not by itself demonstrate that it "
                "caused the observed LST change. LST also "
                "depends on weather, acquisition conditions, "
                "surface moisture, seasonality, and the "
                "available Landsat observations."
            )