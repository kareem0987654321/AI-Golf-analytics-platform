import json

from urllib.parse import quote

from urllib.request import Request, urlopen


from handicap_calculator import HandicapCalculator

from strokes_gained import (
    add_sg_round,
    calculate_average_sg,
    calculate_sg_trend
)

from ai_coach import (
    analyze_player,
    create_ai_context,
    get_initial_ai_analysis,
    ask_ai
)

def search_courses(course_name):

    encoded_name = quote(course_name)

    url = (
        "https://api.golfcore.org/v1/courses"
        f"?q={encoded_name}&limit=5"
    )

    request = Request(
        url,
        headers={
            "User-Agent": "GolfAI/1.0"
        }
    )

    try:

        with urlopen(request) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        return data

    except Exception as error:

        print(f"Course lookup error: {error}")

        return None

def get_course_details(course_slug):

    url = (
        "https://api.golfcore.org/v1/courses/"
        + course_slug
    )

    request = Request(
        url,
        headers={
            "User-Agent": "GolfAI/1.0"
        }
    )

    try:

        with urlopen(request) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

        return data

    except Exception as error:

        print(f"Course details error: {error}")

        return None


def get_yes_no_input(prompt):

    while True:

        value = input(prompt).lower()

        if value in ["y", "yes"]:
            return True

        if value in ["n", "no"]:
            return False

        print("Please enter y or n.")

        
def get_player_round():

    player_name = input("\nPlayer name: ")

    handicap_round = get_handicap_round_input()

    has_shot_data = get_yes_no_input(
        "\nDo you have shot-by-shot data? (y/n): "
    )

    if has_shot_data:
        sg_round = get_sg_round_input()
    else:
        sg_round = None

    return {
        "name": player_name,
        "handicap_round": handicap_round,
        "sg_round": sg_round
    }


def get_list_input(prompt, count, minimum, maximum):

    while True:

        values = input(prompt).split()

        if len(values) != count:
            print(f"Please enter exactly {count} values.")
            continue

        try:
            values = [int(value) for value in values]
        except ValueError:
            print("Please enter whole numbers separated by spaces.")
            continue

        if any(value < minimum or value > maximum for value in values):
            print(
                f"Each value must be between "
                f"{minimum} and {maximum}."
            )
            continue

        return values

    
def get_integer_input(prompt, minimum=None, maximum=None):

    while True:

        try:
            value = int(input(prompt))

            if minimum is not None and value < minimum:
                print(f"Enter a value of at least {minimum}.")
                continue

            if maximum is not None and value > maximum:
                print(f"Enter a value no greater than {maximum}.")
                continue

            return value

        except ValueError:
            print("Please enter a valid whole number.")


def get_float_input(prompt, minimum=None, maximum=None):

    while True:

        try:
            value = float(input(prompt))

            if minimum is not None and value < minimum:
                print(f"Enter a value of at least {minimum}.")
                continue

            if maximum is not None and value > maximum:
                print(f"Enter a value no greater than {maximum}.")
                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


def get_choice_input(prompt, choices):

    while True:

        value = input(prompt).lower()

        if value in choices:
            return value

        print(
            "Please enter one of:",
            ", ".join(choices)
        )



course_name = input(
    "Enter a golf course to search: "
)

course_results = search_courses(
    course_name

)

print("\n--- Course Search Results ---")
print(course_results)


if course_results:

    first_course = course_results["courses"][0]

    course_slug = first_course["slug"]

    course_details = get_course_details(
        course_slug
    )

    print("\n--- Course Details ---")
    print(course_details)

    
def get_handicap_round_input():

    course = input("Course name: ")
    date = input("Date (YYYY-MM-DD): ")

    holes = get_list_input(
        "\nEnter 18 scores separated by spaces: ",
        18,
        1,
        20
    )

    pars = get_list_input(
        "Enter 18 pars separated by spaces: ",
        18,
        3,
        6
    )

    stroke_index = get_list_input(
        "Enter 18 stroke indexes separated by spaces: ",
        18,
        1,
        18
    )

    course_rating = get_float_input(
        "\nCourse Rating: ",
        60,
        80
    )

    slope_rating = get_float_input(
        "Slope Rating: ",
        55,
        155
    )

    par = get_integer_input(
        "Course Par: ",
        54,
        90
    )

    pcc = get_float_input(
        "PCC (enter 0 if unknown): ",
        -1,
        3
    )

    return {
        "course": course,
        "date": date,
        "holes": holes,
        "pars": pars,
        "stroke_index": stroke_index,
        "course_rating": course_rating,
        "slope_rating": slope_rating,
        "par": par,
        "pcc": pcc
    }

def get_sg_round_input():

    sg_round = []

    for hole_number in range(1, 19):

        print(f"\n--- Hole {hole_number} ---")

        number_of_shots = get_integer_input(
            "Number of shots: ",
            1,
            10
        )

        hole = []

        for shot_number in range(1, number_of_shots + 1):

            while True:

                print(
                    "\nEnter:"
                    " starting_distance"
                    " ending_distance"
                    " strokes"
                    " category"
                    " starting_lie"
                    " ending_lie"
                )

                print(
                    "Example:"
                    " 400 150 1 off_the_tee tee fairway"
                )

                values = input(
                    f"Shot {shot_number}: "
                ).split()

                if len(values) != 6:

                    print(
                        "Please enter exactly 6 values."
                    )

                    continue

                try:

                    starting_distance = float(
                        values[0]
                    )

                    ending_distance = float(
                        values[1]
                    )

                    strokes = int(
                        values[2]
                    )

                except ValueError:

                    print(
                        "Distance must be a number "
                        "and strokes must be a whole number."
                    )

                    continue

                category = values[3].lower()
                starting_lie = values[4].lower()
                ending_lie = values[5].lower()

                valid_categories = [
                    "off_the_tee",
                    "approach",
                    "around_the_green",
                    "putting"
                ]

                valid_starting_lies = [
                    "tee",
                    "fairway",
                    "rough",
                    "bunker",
                    "green"
                ]

                valid_ending_lies = [
                    "fairway",
                    "rough",
                    "bunker",
                    "green",
                    "hole"
                ]

                if starting_distance < 0:
                    print(
                        "Starting distance cannot be negative."
                    )
                    continue

                if ending_distance < 0:
                    print(
                        "Ending distance cannot be negative."
                    )
                    continue

                if strokes < 1:
                    print(
                        "Strokes must be at least 1."
                    )
                    continue

                if category not in valid_categories:
                    print(
                        "Invalid category."
                    )
                    continue

                if starting_lie not in valid_starting_lies:
                    print(
                        "Invalid starting lie."
                    )
                    continue

                if ending_lie not in valid_ending_lies:
                    print(
                        "Invalid ending lie."
                    )
                    continue

                break

            shot = {
                "starting_distance": starting_distance,
                "ending_distance": ending_distance,
                "strokes": strokes,
                "category": category,
                "starting_lie": starting_lie,
                "ending_lie": ending_lie
            }

            hole.append(shot)

        sg_round.append(hole)

    return sg_round
    
player_round = get_player_round()

player_name = player_round["name"]

handicap_round1 = player_round["handicap_round"]

sg_round = player_round["sg_round"]


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

calculator.round_history = (
    handicap_round_history.copy()
)


result, new_handicap, esr = (
    calculator.add_round(
        handicap_round1
    )
)


if sg_round is not None:

    add_sg_round(sg_round)



if sg_round is not None:

    strokes_gained_data = {
        "averages": calculate_average_sg(),

        "trends": {
            "total": calculate_sg_trend("total"),
            "off_the_tee": calculate_sg_trend(
                "off_the_tee"
            ),
            "approach": calculate_sg_trend(
                "approach"
            ),
            "around_the_green": calculate_sg_trend(
                "around_the_green"
            ),
            "putting": calculate_sg_trend(
                "putting"
            )
        }
    }

else:

    strokes_gained_data = None


player_data = {

    "name": player_name,

    "handicap": {

        "index":
            calculator.get_handicap_index(),

        "low_handicap":
            calculator.get_low_handicap_index()
    },

    "strokes_gained":
        strokes_gained_data
}


analysis = analyze_player(
    player_data
)


ai_context = create_ai_context(
    player_data,
    analysis
)


initial_analysis = get_initial_ai_analysis(
    ai_context
)

print("\n--- AI Golf Analysis ---")
print(initial_analysis)


conversation_history = []


while True:

    user_question = input(
        "\nAsk the AI a golf question "
        "(type 'quit' to exit): "
    )

    if user_question.lower() == "quit":
        break

    ai_answer = ask_ai(
        ai_context,
        user_question,
        conversation_history
    )

    conversation_history.append({
        "role": "user",
        "content": user_question
    })

    conversation_history.append({
        "role": "assistant",
        "content": ai_answer
    })

    print("\n--- AI Golf Coach ---")
    print(ai_answer)