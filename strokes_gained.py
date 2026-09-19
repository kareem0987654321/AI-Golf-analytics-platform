expected_strokes = {
    500: 4.5,
    400: 4.0,
    300: 3.5,
    200: 3.0,
    150: 2.8,
    100: 2.5,
    50: 2.2,
    30: 2.0,
    20: 1.9,
    10: 1.5,
    5: 1.3,
    0: 0.0
}


def get_expected_strokes(distance, lie):

    distances = sorted(
        expected_strokes.keys(),
        reverse=True
    )

    if distance in expected_strokes:

        base_expected_strokes = (
            expected_strokes[distance]
        )

    elif distance >= distances[0]:

        base_expected_strokes = (
            expected_strokes[distances[0]]
        )

    elif distance <= distances[-1]:

        base_expected_strokes = (
            expected_strokes[distances[-1]]
        )

    else:

        for i in range(len(distances) - 1):

            upper_distance = distances[i]

            lower_distance = distances[i + 1]

            if (
                lower_distance
                <= distance
                <= upper_distance
            ):

                upper_expected = (
                    expected_strokes[upper_distance]
                )

                lower_expected = (
                    expected_strokes[lower_distance]
                )

                ratio = (
                    (upper_distance - distance)
                    /
                    (upper_distance - lower_distance)
                )

                base_expected_strokes = (
                    upper_expected
                    -
                    ratio
                    *
                    (
                        upper_expected
                        -
                        lower_expected
                    )
                )

                break

    lie_adjustments = {
        "tee": 0.0,
        "fairway": 0.0,
        "rough": 0.2,
        "bunker": 0.4,
        "green": 0.0,
        "hole": 0.0
    }

    return (
        base_expected_strokes
        + lie_adjustments[lie]
    )


def calculate_strokes_gained(shot):

    expected_before = get_expected_strokes(
        shot["starting_distance"],
        shot["starting_lie"]
    )

    expected_after = get_expected_strokes(
        shot["ending_distance"],
        shot["ending_lie"]
    )

    strokes_gained = (
        expected_before
        - expected_after
        - shot["strokes"]
    )

    return strokes_gained


def calculate_hole_strokes_gained(hole):

    total_strokes_gained = 0.0

    for shot in hole:

        total_strokes_gained += (
            calculate_strokes_gained(shot)
        )

    return total_strokes_gained


def calculate_round_strokes_gained(round_data):

    total_strokes_gained = 0.0

    for hole in round_data:

        total_strokes_gained += (
            calculate_hole_strokes_gained(hole)
        )

    return total_strokes_gained


def calculate_category_strokes_gained(
    round_data,
    category
):

    total_strokes_gained = 0.0

    for hole in round_data:

        for shot in hole:

            if shot["category"] == category:

                total_strokes_gained += (
                    calculate_strokes_gained(shot)
                )

    return total_strokes_gained


sg_history = []


def add_sg_round(round_data):

    round_sg = {

        "total":
            calculate_round_strokes_gained(
                round_data
            ),

        "off_the_tee":
            calculate_category_strokes_gained(
                round_data,
                "off_the_tee"
            ),

        "approach":
            calculate_category_strokes_gained(
                round_data,
                "approach"
            ),

        "around_the_green":
            calculate_category_strokes_gained(
                round_data,
                "around_the_green"
            ),

        "putting":
            calculate_category_strokes_gained(
                round_data,
                "putting"
            )
    }

    sg_history.append(round_sg)


def calculate_average_sg():

    if len(sg_history) == 0:
        return None

    categories = [
        "total",
        "off_the_tee",
        "approach",
        "around_the_green",
        "putting"
    ]

    averages = {}

    for category in categories:

        total = sum(
            round_sg[category]
            for round_sg in sg_history
        )

        averages[category] = (
            total / len(sg_history)
        )

    return averages


def calculate_sg_trend(category):

    if len(sg_history) < 2:
        return None

    previous_rounds = sg_history[:-1]

    latest_round = sg_history[-1]

    previous_average = sum(
        round_sg[category]
        for round_sg in previous_rounds
    ) / len(previous_rounds)

    latest_value = latest_round[category]

    return latest_value - previous_average
