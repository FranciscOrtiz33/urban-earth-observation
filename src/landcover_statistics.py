import ee

from src.config import ANALYSIS_SCALE



CLASS_NAMES = {
    1: "Vegetation",
    2: "Built-up",
    3: "Bare soil / sparse vegetation",
    4: "Water",
}


def calculate_landcover_areas(
    classified_image,
    roi,
):
    """
    Calculate area in hectares for each
    predicted land-cover class.
    """

    area_image = (
        ee.Image.pixelArea()
        .divide(10000)
        .rename("area_ha")
        .addBands(
            classified_image.rename("landcover")
        )
    )

    stats = area_image.reduceRegion(
        reducer=ee.Reducer.sum().group(
            groupField=1,
            groupName="class",
        ),
        geometry=roi,
        scale=ANALYSIS_SCALE,
        maxPixels=1e13,
        tileScale=4,
    ).getInfo()

    areas = {
        class_name: 0.0
        for class_name in CLASS_NAMES.values()
    }

    for item in stats.get("groups", []):

        class_value = int(item["class"])

        if class_value in CLASS_NAMES:

            areas[
                CLASS_NAMES[class_value]
            ] = item["sum"]

    return areas

def calculate_multiyear_areas(
    classified_maps,
    roi,
):
    """
    Calculate land-cover areas for
    all classified years.
    """

    results = {}

    for year, image in classified_maps.items():

        results[year] = calculate_landcover_areas(
            classified_image=image,
            roi=roi,
        )

    return results

def calculate_transition_matrix(
    start_image,
    end_image,
    roi,
):
    """
    Calculate land-cover transitions in hectares
    between two classified maps.

    Rows represent the initial class.
    Columns represent the final class.
    """

    transition = (
        start_image
        .multiply(10)
        .add(end_image)
        .rename("transition")
    )

    area_image = (
        ee.Image.pixelArea()
        .divide(10000)
        .rename("area_ha")
        .addBands(transition)
    )

    stats = area_image.reduceRegion(
        reducer=ee.Reducer.sum().group(
            groupField=1,
            groupName="transition",
        ),
        geometry=roi,
        scale=ANALYSIS_SCALE,
        maxPixels=1e13,
        tileScale=4,
    ).getInfo()

    matrix = {
        start_name: {
            end_name: 0.0
            for end_name in CLASS_NAMES.values()
        }
        for start_name in CLASS_NAMES.values()
    }

    for item in stats.get("groups", []):

        code = int(item["transition"])

        start_class = code // 10
        end_class = code % 10

        if (
            start_class in CLASS_NAMES
            and end_class in CLASS_NAMES
        ):

            matrix[
                CLASS_NAMES[start_class]
            ][
                CLASS_NAMES[end_class]
            ] = item["sum"]

    return matrix

def calculate_period_transition(
    classified_maps,
    roi,
):
    """
    Calculate transitions between the earliest
    and latest classified years.
    """

    years = sorted(classified_maps.keys())

    if len(years) < 2:
        raise ValueError(
            "At least two years are required "
            "to calculate transitions."
        )

    start_year = years[0]
    end_year = years[-1]

    matrix = calculate_transition_matrix(
        start_image=classified_maps[start_year],
        end_image=classified_maps[end_year],
        roi=roi,
    )

    return start_year, end_year, matrix

def calculate_net_changes(
    multiyear_areas,
):
    """
    Calculate net land-cover change between
    the earliest and latest analyzed years.
    """

    years = sorted(multiyear_areas.keys())

    if len(years) < 2:
        raise ValueError(
            "At least two years are required "
            "to calculate net changes."
        )

    start_year = years[0]
    end_year = years[-1]

    start_areas = multiyear_areas[start_year]
    end_areas = multiyear_areas[end_year]

    changes = {}

    for class_name in CLASS_NAMES.values():

        start_area = start_areas[class_name]
        end_area = end_areas[class_name]

        absolute_change = (
            end_area - start_area
        )

        if start_area > 0:

            percent_change = (
                absolute_change
                / start_area
                * 100
            )

        else:
            percent_change = None

        changes[class_name] = {
            "start_area_ha": start_area,
            "end_area_ha": end_area,
            "change_ha": absolute_change,
            "change_percent": percent_change,
        }

    return start_year, end_year, changes

def calculate_gains_losses(
    transition_matrix,
):
    """
    Calculate gross gains, losses and net change
    for each land-cover class.
    """

    classes = list(
        transition_matrix.keys()
    )

    results = {}

    for class_name in classes:

        stable = transition_matrix[
            class_name
        ][
            class_name
        ]

        losses = sum(
            transition_matrix[
                class_name
            ][
                target_class
            ]
            for target_class in classes
            if target_class != class_name
        )

        gains = sum(
            transition_matrix[
                source_class
            ][
                class_name
            ]
            for source_class in classes
            if source_class != class_name
        )

        results[class_name] = {
            "stable_ha": stable,
            "gains_ha": gains,
            "losses_ha": losses,
            "net_change_ha": gains - losses,
        }

    return results