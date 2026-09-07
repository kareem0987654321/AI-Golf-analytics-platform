from openai import OpenAI

import os

client = OpenAI()

print(
    "API key found!"
    if os.getenv("OPENAI_API_KEY")
    else "API key NOT found"
)
# HANDICAP CALCULATOR/////////////////
#/////////////////////////////
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

    # Need at least 3 rounds
    if len(differentials) < 3:
        return None

    # Only use most recent 20 rounds
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


handicap_round1 = {

    "course": "Example Golf Club",

    "date": "2026-09-05",

    "holes": [
        5, 4, 5, 6, 4, 5, 4, 6, 5,
        4, 5, 4, 6, 5, 4, 5, 6, 5
    ],

    "pars": [
        4, 4, 5, 4, 4, 5, 3, 5, 4,
        4, 5, 4, 4, 5, 3, 4, 5, 4
    ],

    "stroke_index": [
        5, 1, 15, 3, 7, 11, 9, 13, 17,
        6, 2, 16, 4, 8, 18, 10, 14, 12
    ],

    "course_rating": 72.5,
    "slope_rating": 130,
    "par": 72,
    "pcc": 0
}


handicap_round_history = [

    {
        "course": "Example Golf Club",
        "date": "2026-08-20",
        "adjusted_score": 82,
        "course_rating": 72.5,
        "slope_rating": 130,
        "pcc": 0
    },

    {
        "course": "Example Golf Club",
        "date": "2026-08-25",
        "adjusted_score": 84,
        "course_rating": 72.5,
        "slope_rating": 130,
        "pcc": 0
    },

    {
        "course": "Example Golf Club",
        "date": "2026-08-28",
        "adjusted_score": 80,
        "course_rating": 72.5,
        "slope_rating": 130,
        "pcc": 0
    }
]



calculator = HandicapCalculator()

calculator.round_history = handicap_round_history.copy()

result, new_handicap, esr = calculator.add_round(
    handicap_round1
)



for round_data in calculator.round_history:

    differential = get_round_differential(
        round_data
    )




# strokes gained code
# /////////////////////////////////////////////////////////



shot1 = {

    "starting_distance": 150,

    "ending_distance": 20,

    "strokes": 1,

    "starting_lie": "fairway",

    "ending_lie": "green"
}


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


print("\n--- Shot Data ---")

print(shot1)

print(
    f"Strokes Gained: "
    f"{calculate_strokes_gained(shot1):.2f}"
)


# 18 HOLE round 

round1 = [

    # Hole 1
    [
        {
            "starting_distance": 400,
            "ending_distance": 150,
            "strokes": 1,
            "category": "off_the_tee",
            "starting_lie": "tee",
            "ending_lie": "fairway"
        },

        {
            "starting_distance": 150,
            "ending_distance": 20,
            "strokes": 1,
            "category": "approach",
            "starting_lie": "fairway",
            "ending_lie": "green"
        },

        {
            "starting_distance": 20,
            "ending_distance": 5,
            "strokes": 1,
            "category": "around_the_green",
            "starting_lie": "rough",
            "ending_lie": "green"
        },

        {
            "starting_distance": 5,
            "ending_distance": 0,
            "strokes": 1,
            "category": "putting",
            "starting_lie": "green",
            "ending_lie": "hole"
        }
    ],

    # Hole 2
    [
        {
            "starting_distance": 500,
            "ending_distance": 250,
            "strokes": 1,
            "category": "off_the_tee",
            "starting_lie": "tee",
            "ending_lie": "rough"
        },

        {
            "starting_distance": 250,
            "ending_distance": 100,
            "strokes": 1,
            "category": "approach",
            "starting_lie": "rough",
            "ending_lie": "fairway"
        },

        {
            "starting_distance": 100,
            "ending_distance": 15,
            "strokes": 1,
            "category": "approach",
            "starting_lie": "fairway",
            "ending_lie": "green"
        },

        {
            "starting_distance": 15,
            "ending_distance": 0,
            "strokes": 2,
            "category": "putting",
            "starting_lie": "green",
            "ending_lie": "hole"
        }
    ],

    # Hole 3
    [
        {
            "starting_distance": 150,
            "ending_distance": 50,
            "strokes": 1,
            "category": "off_the_tee",
            "starting_lie": "tee",
            "ending_lie": "rough"
        },

        {
            "starting_distance": 50,
            "ending_distance": 10,
            "strokes": 1,
            "category": "around_the_green",
            "starting_lie": "rough",
            "ending_lie": "green"
        },

        {
            "starting_distance": 10,
            "ending_distance": 0,
            "strokes": 2,
            "category": "putting",
            "starting_lie": "green",
            "ending_lie": "hole"
        }
    ],

    # Hole 4
    [
        {
            "starting_distance": 400,
            "ending_distance": 200,
            "strokes": 1,
            "category": "off_the_tee",
            "starting_lie": "tee",
            "ending_lie": "fairway"
        },

        {
            "starting_distance": 200,
            "ending_distance": 30,
            "strokes": 1,
            "category": "approach",
            "starting_lie": "fairway",
            "ending_lie": "green"
        },

        {
            "starting_distance": 30,
            "ending_distance": 0,
            "strokes": 2,
            "category": "putting",
            "starting_lie": "green",
            "ending_lie": "hole"
        }
    ],

    # Hole 5
    [
        {
            "starting_distance": 450,
            "ending_distance": 250,
            "strokes": 1,
            "category": "off_the_tee",
            "starting_lie": "tee",
            "ending_lie": "fairway"
        },

        {
            "starting_distance": 250,
            "ending_distance": 120,
            "strokes": 1,
            "category": "approach",
            "starting_lie": "fairway",
            "ending_lie": "rough"
        },

        {
            "starting_distance": 120,
            "ending_distance": 20,
            "strokes": 2,
            "category": "approach",
            "starting_lie": "rough",
            "ending_lie": "green"
        },

        {
            "starting_distance": 20,
            "ending_distance": 0,
            "strokes": 2,
            "category": "putting",
            "starting_lie": "green",
            "ending_lie": "hole"
        }
    ]
]


# Repeat some holes to create an 18-hole test round
while len(round1) < 18:
    round1.append(round1[len(round1) % 5])


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

        "total": calculate_round_strokes_gained(
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


# ///////////////////////////////////////////////////////////
# STROKES GAINED CODE
# /////////////////////////////////////////////////////////////////

add_sg_round(round1)

# Temporary second round for testing history
add_sg_round(round1)


print("\n--- SG Round History ---")

for i, round_sg in enumerate(
    sg_history,
    start=1
):

    averages = calculate_average_sg()



for category in [
    "total",
    "off_the_tee",
    "approach",
    "around_the_green",
    "putting"
]:

    print(
        f"{category}: "
        f"{calculate_sg_trend(category):.2f}"
    )


# ============================================================
# AI DATA LAYER
# ============================================================

def analyze_player(player_data):

    averages = (
        player_data["strokes_gained"]["averages"]
    )

    categories = {

        "off_the_tee":
            averages["off_the_tee"],

        "approach":
            averages["approach"],

        "around_the_green":
            averages["around_the_green"],

        "putting":
            averages["putting"]
    }

    strongest_category = max(
        categories,
        key=categories.get
    )

    weakest_category = min(
        categories,
        key=categories.get
    )

    return {

        "strongest_area":
            strongest_category,

        "strongest_value":
            categories[strongest_category],

        "weakest_area":
            weakest_category,

        "weakest_value":
            categories[weakest_category]
    }


player_data = {

    "name": "Test Golfer",

    "handicap": {

        "index":
            calculator.get_handicap_index(),

        "low_handicap":
            calculator.get_low_handicap_index()
    },

    "strokes_gained": {

        "averages":
            calculate_average_sg(),

        "trends": {

            "total":
                calculate_sg_trend("total"),

            "off_the_tee":
                calculate_sg_trend(
                    "off_the_tee"
                ),

            "approach":
                calculate_sg_trend(
                    "approach"
                ),

            "around_the_green":
                calculate_sg_trend(
                    "around_the_green"
                ),

            "putting":
                calculate_sg_trend(
                    "putting"
                )
        }
    }
}


analysis = analyze_player(
    player_data
)


def create_ai_context(
    player_data,
    analysis
):

    context = f"""
You are a golf performance analyst.

Player:
{player_data['name']}

Handicap Index:
{player_data['handicap']['index']}

Low Handicap:
{player_data['handicap']['low_handicap']}

Average Strokes Gained:

Off the Tee:
{player_data['strokes_gained']['averages']['off_the_tee']:.2f}

Approach:
{player_data['strokes_gained']['averages']['approach']:.2f}

Around the Green:
{player_data['strokes_gained']['averages']['around_the_green']:.2f}

Putting:
{player_data['strokes_gained']['averages']['putting']:.2f}

Strongest Area:
{analysis['strongest_area']}
({analysis['strongest_value']:.2f})

Weakest Area:
{analysis['weakest_area']}
({analysis['weakest_value']:.2f})
"""

    return context


ai_context = create_ai_context(
    player_data,
    analysis
)


print(player_data)



print(ai_context)

response = client.responses.create(
    model="gpt-5.6",
    input=ai_context
)

print("\n--- AI Golf Analysis ---")
print(response.output_text)

conversation_history = []

while True:

    user_question = input(
        "\nAsk the AI a golf question: "
    )

    response = client.responses.create(
        model="gpt-5.6",
        input=f"""
    You are an AI golf performance coach.

    Use the player's statistics below to answer the player's question.

    PLAYER DATA:
    {ai_context}

    PLAYER QUESTION:
    {user_question}

    Structure your response using these sections:

    1. Strengths
    Identify what the player is doing well based on the data.

    2. Weakness
    Identify the most important area that is costing the player strokes.

    3. Analysis
    Explain why the data suggests this is an important area to work on.

    4. Practice Recommendation
    Give 2-3 specific practice ideas the player can use.

    Base your answer on the player's actual statistics.
    Do not invent statistics that are not provided.
    """
    )

    print("\n--- AI Golf Coach ---")
    print(response.output_text)