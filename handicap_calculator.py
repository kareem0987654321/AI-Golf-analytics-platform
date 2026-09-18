def calculate_total_score(holes):
    return sum(holes)


def calculate_net_double_bogey(par, strokes_received):
    return par + 2 + strokes_received


def calculate_adjusted_gross_score(
    holes,
    pars,
    strokes_received
):
    adjusted_scores = []

    for i in range(len(holes)):

        maximum_score = calculate_net_double_bogey(
            pars[i],
            strokes_received[i]
        )

        adjusted_score = min(
            holes[i],
            maximum_score
        )

        adjusted_scores.append(adjusted_score)

    return sum(adjusted_scores)


def calculate_score_differential(
    adjusted_score,
    course_rating,
    slope_rating,
    pcc=0
):
    differential = (
        (adjusted_score - course_rating - pcc)
        * 113
        / slope_rating
    )

    return differential


def calculate_strokes_received(
    course_handicap,
    stroke_index
):
    strokes_received = []

    for si in stroke_index:

        strokes = course_handicap // 18

        if si <= (course_handicap % 18):
            strokes += 1

        strokes_received.append(strokes)

    return strokes_received


def calculate_course_handicap(
    handicap_index,
    slope_rating,
    course_rating,
    par
):
    course_handicap = (
        handicap_index
        * (slope_rating / 113)
        + (course_rating - par)
    )

    return round(course_handicap)


def calculate_handicap_index(differentials):

    if len(differentials) < 3:
        return None

    recent_differentials = differentials[-20:]

    number_of_scores = len(recent_differentials)

    differentials_to_use = {
        3: 1,
        4: 1,
        5: 1,
        6: 2,
        7: 2,
        8: 2,
        9: 3,
        10: 3,
        11: 3,
        12: 4,
        13: 4,
        14: 4,
        15: 5,
        16: 5,
        17: 6,
        18: 6,
        19: 7,
        20: 8
    }

    count = differentials_to_use[number_of_scores]

    sorted_differentials = sorted(
        recent_differentials
    )

    best_differentials = sorted_differentials[:count]

    handicap_index = (
        sum(best_differentials) / count
    )

    return round(handicap_index, 1)


def calculate_exceptional_score_reduction(
    score_differential,
    handicap_index
):
    difference = (
        handicap_index - score_differential
    )

    if difference >= 10.0:
        return -2.0

    elif difference >= 7.0:
        return -1.0

    else:
        return 0.0


def process_round(round_data, handicap_index):

    course_handicap = calculate_course_handicap(
        handicap_index,
        round_data["slope_rating"],
        round_data["course_rating"],
        round_data["par"]
    )

    strokes_received = calculate_strokes_received(
        course_handicap,
        round_data["stroke_index"]
    )

    raw_score = calculate_total_score(
        round_data["holes"]
    )

    adjusted_score = calculate_adjusted_gross_score(
        round_data["holes"],
        round_data["pars"],
        strokes_received
    )

    differential = calculate_score_differential(
        adjusted_score,
        round_data["course_rating"],
        round_data["slope_rating"],
        round_data["pcc"]
    )

    return {
        "course_handicap": course_handicap,
        "strokes_received": strokes_received,
        "raw_score": raw_score,
        "adjusted_score": adjusted_score,
        "score_differential": differential
    }


def get_round_differential(round_data):

    return calculate_score_differential(
        round_data["adjusted_score"],
        round_data["course_rating"],
        round_data["slope_rating"],
        round_data.get("pcc", 0)
    )


class HandicapCalculator:

    def __init__(self):

        self.round_history = []
        self.low_handicap_index = None

    def get_differentials(self):

        differentials = []

        for round_data in self.round_history:

            differential = get_round_differential(
                round_data
            )

            differentials.append(differential)

        return differentials

    def get_handicap_index(self):

        differentials = self.get_differentials()

        if len(differentials) < 3:
            return None

        handicap_index = calculate_handicap_index(
            differentials
        )

        if handicap_index > 54.0:
            handicap_index = 54.0

        return handicap_index

    def get_low_handicap_index(self):

        current_handicap = self.get_handicap_index()

        if current_handicap is None:
            return None

        if self.low_handicap_index is None:
            self.low_handicap_index = current_handicap

        elif current_handicap < self.low_handicap_index:
            self.low_handicap_index = current_handicap

        return self.low_handicap_index

    def add_round(self, round_data):

        current_handicap = self.get_handicap_index()

        if current_handicap is None:
            current_handicap = 0.0

        result = process_round(
            round_data,
            current_handicap
        )

        new_round = {
            "course": round_data["course"],
            "date": round_data["date"],
            "score": result["raw_score"],
            "adjusted_score": result["adjusted_score"],
            "course_rating": round_data["course_rating"],
            "slope_rating": round_data["slope_rating"],
            "pcc": round_data.get("pcc", 0)
        }

        self.round_history.append(new_round)

        if len(self.round_history) > 20:
            self.round_history = self.round_history[-20:]

        new_handicap = self.get_handicap_index()

        self.get_low_handicap_index()

        return result, new_handicap, 0.0
