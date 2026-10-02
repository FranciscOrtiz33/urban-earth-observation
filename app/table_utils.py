import pandas as pd


def build_confusion_dataframe(
    metrics,
    class_names,
):
    """Build the model confusion-matrix DataFrame."""

    return pd.DataFrame(
        metrics["matrix"],
        index=class_names,
        columns=class_names,
    )


def build_area_dataframe(areas):
    """Build the multiyear land-cover area table."""

    dataframe = (
        pd.DataFrame(areas)
        .T
        .sort_index()
    )

    dataframe.index.name = "Year"

    return dataframe.round(2)


def build_sentinel_metadata_dataframe(metadata):
    """Build the Sentinel-2 observation metadata table."""

    rows = []

    for year, info in metadata.items():
        rows.append({
            "Year": year,
            "Sentinel-2 scenes": info["scene_count"],
            "Start date": info["start_date"],
            "End date": info["end_date"],
        })

    return (
        pd.DataFrame(rows)
        .sort_values("Year")
        .set_index("Year")
    )


def build_net_change_dataframe(
    net_changes,
    start_year,
    end_year,
):
    """Build the net land-cover change table."""

    rows = []

    for class_name, values in net_changes.items():
        rows.append({
            "Class": class_name,
            f"{start_year} (ha)": values["start_area_ha"],
            f"{end_year} (ha)": values["end_area_ha"],
            "Change (ha)": values["change_ha"],
            "Change (%)": values["change_percent"],
        })

    return (
        pd.DataFrame(rows)
        .set_index("Class")
    )


def build_gains_losses_dataframe(
    gains_losses,
):
    """Build the gross gains/losses table."""

    rows = []

    for class_name, values in gains_losses.items():
        rows.append({
            "Class": class_name,
            "Stable (ha)": values["stable_ha"],
            "Gains (ha)": values["gains_ha"],
            "Losses (ha)": values["losses_ha"],
            "Net change (ha)": values["net_change_ha"],
        })

    return (
        pd.DataFrame(rows)
        .set_index("Class")
    )


def build_transition_dataframe(
    transition_matrix,
    class_names,
    start_year,
    end_year,
):
    """Build the land-cover transition matrix DataFrame."""

    dataframe = (
        pd.DataFrame(
            transition_matrix
        )
        .T
    )

    dataframe = dataframe[
        class_names
    ]

    dataframe.index.name = (
        f"From ({start_year})"
    )

    dataframe.columns.name = (
        f"To ({end_year})"
    )

    return dataframe


def build_thermal_statistics_dataframe(
    statistics,
):
    """Build the single-year LST statistics table."""

    rows = []

    for class_name, stats in statistics.items():
        rows.append({
            "Land cover": class_name,
            "Mean LST (°C)": stats["mean_c"],
            "Median LST (°C)": stats["median_c"],
            "Minimum LST (°C)": stats["min_c"],
            "Maximum LST (°C)": stats["max_c"],
            "Valid pixels": stats["valid_pixels"],
        })

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .set_index("Land cover")
    )


def build_multiyear_thermal_dataframe(
    multiyear_thermal,
    class_names,
    statistic_key,
):
    """
    Build a multiyear thermal table.

    statistic_key examples:
    - "mean_c"
    - "median_c"
    """

    rows = []

    for year in sorted(
        multiyear_thermal.keys()
    ):
        row = {
            "Year": year,
        }

        year_statistics = (
            multiyear_thermal[
                year
            ][
                "statistics"
            ]
        )

        for class_name in class_names:
            stats = year_statistics.get(
                class_name
            )

            row[class_name] = (
                None
                if stats is None
                else stats.get(
                    statistic_key
                )
            )

        rows.append(row)

    return (
        pd.DataFrame(rows)
        .set_index("Year")
    )


def build_temperature_difference_dataframe(
    thermal_mean_df,
    reference_class="Vegetation",
):
    """
    Calculate class temperature differences relative
    to a reference class.
    """

    comparison_classes = [
        column
        for column in thermal_mean_df.columns
        if column != reference_class
    ]

    rows = []

    for year in thermal_mean_df.index:
        reference_temperature = (
            thermal_mean_df.loc[
                year,
                reference_class,
            ]
        )

        row = {
            "Year": year,
        }

        for class_name in comparison_classes:
            class_temperature = (
                thermal_mean_df.loc[
                    year,
                    class_name,
                ]
            )

            if (
                pd.notna(
                    reference_temperature
                )
                and pd.notna(
                    class_temperature
                )
            ):
                row[class_name] = (
                    class_temperature
                    - reference_temperature
                )
            else:
                row[class_name] = None

        rows.append(row)

    return (
        pd.DataFrame(rows)
        .set_index("Year")
    )


def build_landsat_metadata_dataframe(
    multiyear_thermal,
):
    """Build the Landsat observation metadata table."""

    rows = []

    for year in sorted(
        multiyear_thermal.keys()
    ):
        year_result = (
            multiyear_thermal[
                year
            ]
        )

        rows.append({
            "Year": year,
            "Landsat scenes":
                year_result[
                    "scene_count"
                ],
            "Start date":
                year_result[
                    "start_date"
                ],
            "End date":
                year_result[
                    "end_date"
                ],
        })

    return (
        pd.DataFrame(rows)
        .set_index("Year")
    )


def build_integrated_change_dataframe(
    areas,
    thermal_mean_df,
    class_names,
):
    """
    Combine first-to-last-year land-cover change
    with first-to-last-year mean LST change.
    """

    first_year = min(
        areas.keys()
    )

    last_year = max(
        areas.keys()
    )

    rows = []

    for class_name in class_names:
        start_area = (
            areas[
                first_year
            ][
                class_name
            ]
        )

        end_area = (
            areas[
                last_year
            ][
                class_name
            ]
        )

        start_temperature = (
            thermal_mean_df.loc[
                first_year,
                class_name,
            ]
        )

        end_temperature = (
            thermal_mean_df.loc[
                last_year,
                class_name,
            ]
        )

        if (
            pd.notna(
                start_temperature
            )
            and pd.notna(
                end_temperature
            )
        ):
            temperature_change = (
                end_temperature
                - start_temperature
            )
        else:
            temperature_change = None

        rows.append({
            "Land cover":
                class_name,
            f"Area {first_year} (ha)":
                start_area,
            f"Area {last_year} (ha)":
                end_area,
            "Area change (ha)":
                end_area - start_area,
            f"Mean LST {first_year} (°C)":
                start_temperature,
            f"Mean LST {last_year} (°C)":
                end_temperature,
            "LST change (°C)":
                temperature_change,
        })

    dataframe = (
        pd.DataFrame(rows)
        .set_index("Land cover")
    )

    return (
        dataframe,
        first_year,
        last_year,
    )


def build_integrated_summary(
    areas,
    thermal_mean_df,
    first_year,
    last_year,
):
    """Build the three summary indicators used by the UI."""

    built_up_area_change = (
        areas[
            last_year
        ][
            "Built-up"
        ]
        -
        areas[
            first_year
        ][
            "Built-up"
        ]
    )

    vegetation_area_change = (
        areas[
            last_year
        ][
            "Vegetation"
        ]
        -
        areas[
            first_year
        ][
            "Vegetation"
        ]
    )

    built_up_lst_start = (
        thermal_mean_df.loc[
            first_year,
            "Built-up",
        ]
    )

    built_up_lst_end = (
        thermal_mean_df.loc[
            last_year,
            "Built-up",
        ]
    )

    if (
        pd.notna(
            built_up_lst_start
        )
        and pd.notna(
            built_up_lst_end
        )
    ):
        built_up_lst_change = (
            built_up_lst_end
            - built_up_lst_start
        )
    else:
        built_up_lst_change = None

    return {
        "built_up_area_change":
            built_up_area_change,
        "vegetation_area_change":
            vegetation_area_change,
        "built_up_lst_change":
            built_up_lst_change,
    }
