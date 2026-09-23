import json

from sklearn.cluster import KMeans

from sklearn.metrics import silhouette_score

from urllib.parse import quote

from urllib.request import Request, urlopen

from handicap_calculator import HandicapCalculator

from pathlib import Path

from strokes_gained import (
    add_sg_round,
    calculate_average_sg,
    calculate_sg_trend,
    calculate_round_strokes_gained,
    calculate_category_strokes_gained
)

from ai_coach import (
    analyze_player,
    create_ai_context,
    get_initial_ai_analysis,
    ask_ai
)

HISTORY_FILE = (
    Path(__file__).parent / "round_history.json"
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

def load_round_history():

    try:

        with open(
            HISTORY_FILE,
            "r"
        ) as file:

            return json.load(file)

    except FileNotFoundError:

        return []


def save_round_history(round_history):

    with open(
        HISTORY_FILE,
        "w"
    ) as file:

        json.dump(
            round_history,
            file,
            indent=4
        )

def create_ml_dataset(round_history):

    dataset = []

    for round_data in round_history:

        sg = round_data.get("strokes_gained")

        # Skip rounds that do not have
        # shot-by-shot Strokes Gained data
        if sg is None:
            continue

        # Make sure all SG categories exist
        required_categories = [
            "off_the_tee",
            "approach",
            "around_the_green",
            "putting"
        ]   

        if not all(
            category in sg
            for category in required_categories
        ):
            continue

        row = [
            sg["off_the_tee"],
            sg["approach"],
            sg["around_the_green"],
            sg["putting"]
        ]

        dataset.append(row)

    return dataset

def choose_number_of_clusters(dataset):

    number_of_rounds = len(dataset)

    # need enough rounds to compare clusters.
    if number_of_rounds < 4:
        return 2

    best_k = 2
    best_score = -1

    #  test between 2 and 5 clusters,
    #  cannot have as many clusters
    # as data points.
    max_clusters = min(
        5,
        number_of_rounds - 1
    )

    for k in range(
        2,
        max_clusters + 1
    ):

        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10
        )

        labels = model.fit_predict(
            dataset
        )

        # Silhouette score requires at least
        # two different clusters.
        if len(set(labels)) < 2:
            continue

        score = silhouette_score(
            dataset,
            labels
        )

        print(
            f"k = {k}, "
            f"Silhouette Score = {score:.3f}"
        )

        if score > best_score:

            best_score = score
            best_k = k

    return best_k

def identify_performance_patterns(dataset):

    if len(dataset) < 3:

        print(
            "\nNot enough Strokes Gained rounds "
            "for ML pattern detection yet."
        )

        print(
            f"Currently have {len(dataset)} "
            "usable SG round(s)."
        )

        return None

    number_of_clusters = (
        choose_number_of_clusters(
            dataset
        )
    )
    print(
        "\nSelected number of pattersn:",
        number_of_clusters
    )

    model = KMeans(
        n_clusters=number_of_clusters,
        random_state=42,
        n_init=10
    )

    model.fit(dataset)

    patterns = []

    feature_names = [
        "Off the Tee",
        "Approach",
        "Around the Green",
        "Putting"
    ]

    print("\n--- ML Performance Patterns ---")

    for cluster_number, center in enumerate(
        model.cluster_centers_
    ):

        print(
            f"\nPattern {cluster_number + 1}:"
        )

        for feature, value in zip(
            feature_names,
            center
        ):

            print(
                f"{feature}: {value:.2f}"
            )

        category_values = center

        strongest_index = max(
            range(len(category_values)),
            key=lambda i: category_values[i]
        )

        weakest_index = min(
            range(len(category_values)),
            key=lambda i: category_values[i]
        )

        category_names = feature_names

        print(
            "Strongest Area:",
            category_names[strongest_index]
        )

        print(
            "Weakest Area:",
            category_names[weakest_index]
        )

        print(
            "\n--- Round Pattern Assignments ---"
        )

        for round_number, label in enumerate(
            model.labels_,
            start=1
        ):

            print(
            f"SG Round {round_number}: "
            f"Pattern {label + 1}"
        )

            
        print(
            "\n--- Pattern Frequency ---"
        )

        pattern_count = sum(
        label == cluster_number
        for label in model.labels_
    )

    pattern_percentage = (
        pattern_count / len(model.labels_)
    ) * 100

    pattern = {
        "pattern_number":
            cluster_number + 1,

        "off_the_tee":
            center[0],

        "approach":
            center[1],

        "around_the_green":
            center[2],

        "putting":
            center[3],

        "strongest_area":
            category_names[strongest_index],

        "strongest_value":
            center[strongest_index],

        "weakest_area":
            category_names[weakest_index],

        "weakest_value":
            center[weakest_index],

        "round_count":
            pattern_count,

        "percentage":
            pattern_percentage
    }

    patterns.append(pattern)    

    total_rounds = len(model.labels_)

    for cluster_number in range(
            number_of_clusters
        ):

            pattern_count = sum(
                label == cluster_number
                for label in model.labels_
            )

            pattern_percentage = (
                pattern_count / total_rounds
            ) * 100

            print(
                f"Pattern {cluster_number + 1}: "
                f"{pattern_count} rounds "
                f"({pattern_percentage:.1f}%)"
            )
    most_common_pattern = max(
        patterns,
        key=lambda pattern:
            pattern["round_count"]
    )

    ml_analysis = {
        "patterns": patterns,

        "most_common_pattern":
            most_common_pattern
    }

    return model, ml_analysis

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

def select_course_tee(course_details):

    layouts = course_details.get("layouts", [])

    if not layouts:
        print("No course layouts were found.")
        return None

    print("\n--- Available Course Layouts ---")

    for i, layout in enumerate(layouts, start=1):

        print(
            f"{i}. "
            f"{layout.get('name', 'Unknown Layout')}"
        )

    while True:

        try:

            layout_selection = int(
                input(
                    f"\nSelect a layout (1-{len(layouts)}): "
                )
            )

            if 1 <= layout_selection <= len(layouts):
                break

            print(
                f"Enter a number from 1 to {len(layouts)}."
            )

        except ValueError:

            print("Please enter a whole number.")

    selected_layout = layouts[
        layout_selection - 1
    ]

    tees = selected_layout.get("tees", [])

    if not tees:
        print("No tees were found.")
        return None

    print("\n--- Available Tees ---")

    for i, tee in enumerate(tees, start=1):

        print(
            f"{i}. "
            f"{tee.get('name', 'Unknown Tee')} "
            f"({tee.get('gender', 'unknown')}) - "
            f"Rating: {tee.get('rating')} | "
            f"Slope: {tee.get('slope')} | "
            f"Par: {tee.get('par')}"
        )

    while True:

        try:

            tee_selection = int(
                input(
                    f"\nSelect a tee (1-{len(tees)}): "
                )
            )

            if 1 <= tee_selection <= len(tees):
                break

            print(
                f"Enter a number from 1 to {len(tees)}."
            )

        except ValueError:

            print("Please enter a whole number.")

    selected_tee = tees[
        tee_selection - 1
    ]

    holes = selected_tee.get("holes", [])

    if len(holes) != 18:

        print(
            "\nWarning: complete 18-hole data "
            "was not found for this tee."
        )

        return None

    pars = [
        hole["par"]
        for hole in holes
    ]

    stroke_index = [
        hole["stroke_index"]
        for hole in holes
    ]

    course_data = {
        "layout": selected_layout.get(
            "name",
            "Unknown Layout"
        ),

        "tee": selected_tee.get(
            "name",
            "Unknown Tee"
        ),

        "gender": selected_tee.get(
            "gender"
        ),

        "course_rating": selected_tee.get(
            "rating"
        ),

        "slope_rating": selected_tee.get(
            "slope"
        ),

        "par": selected_tee.get(
            "par"
        ),

        "pars": pars,

        "stroke_index": stroke_index
    }

    return course_data


def get_yes_no_input(prompt):

    while True:

        value = input(prompt).lower()

        if value in ["y", "yes"]:
            return True

        if value in ["n", "no"]:
            return False

        print("Please enter y or n.")

        
def get_player_round(
    course_name,
    course_data
):

    player_name = input("\nPlayer name: ")

    handicap_round = get_handicap_round_input(
        course_name,
        course_data
    )

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

handicap_round_history = load_round_history()


course_name = input(
    "Enter a golf course to search: "
)

course_results = search_courses(
    course_name

)

print("\n--- Course Search Results ---")

courses = course_results.get("courses", [])

if not courses:

    print("No courses found.")

    course_slug = None
    course_details = None

else:

    for i, course in enumerate(courses, start=1):

        print(
            f"{i}. "
            f"{course.get('name', 'Unknown Course')} "
            f"- "
            f"{course.get('city', '')}, "
            f"{course.get('region', '')}"
        )

    while True:

        try:

            selection = int(
                input(
                    f"\nSelect a course (1-{len(courses)}): "
                )
            )

            if 1 <= selection <= len(courses):
                break

            print(
                f"Enter a number from 1 to {len(courses)}."
            )

        except ValueError:

            print("Please enter a whole number.")

    selected_course = courses[selection - 1]

    course_slug = selected_course["slug"]

    selected_course_name = selected_course.get(
        "name",
        "Unknown Course"
    )

    course_details = get_course_details(
        course_slug
    )

    selected_course_data = select_course_tee(
        course_details
    )

    print("\n--- Selected Course ---")

    print(
        f"Course: "
        f"{selected_course.get('name', 'Unknown')}"
    )

    print(
        f"Location: "
        f"{selected_course.get('city', '')}, "
        f"{selected_course.get('region', '')}"
    )

    
def get_handicap_round_input(
    course_name,
    course_data
):

    date = input("Date (YYYY-MM-DD): ")

    holes = get_list_input(
        "\nEnter your 18 scores separated by spaces: ",
        18,
        1,
        20
    )

    return {
        "course": course_name,
        "date": date,
        "holes": holes,
        "pars": course_data["pars"],
        "stroke_index": course_data["stroke_index"],
        "course_rating": course_data["course_rating"],
        "slope_rating": course_data["slope_rating"],
        "par": course_data["par"],
        "pcc": 0
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
    
player_round = get_player_round(
    selected_course_name,
    selected_course_data
)

player_name = player_round["name"]

handicap_round1 = player_round["handicap_round"]

sg_round = player_round["sg_round"]




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

    round_sg = {
        "total":
            calculate_round_strokes_gained(
                sg_round
            ),

        "off_the_tee":
            calculate_category_strokes_gained(
                sg_round,
                "off_the_tee"
            ),

        "approach":
            calculate_category_strokes_gained(
                sg_round,
                "approach"
            ),

        "around_the_green":
            calculate_category_strokes_gained(
                sg_round,
                "around_the_green"
            ),

        "putting":
            calculate_category_strokes_gained(
                sg_round,
                "putting"
            )
    }

    calculator.round_history[-1][
        "strokes_gained"
    ] = round_sg

else:

    calculator.round_history[-1][
        "strokes_gained"
    ] = None

save_round_history(
    calculator.round_history
)

ml_dataset = create_ml_dataset(
    calculator.round_history
)

print(
    "Usable SG rounds for ML:",
    len(ml_dataset)
)


ml_result = identify_performance_patterns(
    ml_dataset
)

if ml_result is not None:

    ml_model, ml_analysis = ml_result

else:

    ml_model = None
    ml_analysis = None

if ml_analysis is not None:


   # print(ml_analysis)

    if ml_result is not None:
        ml_model, ml_analysis = ml_result

else:
    ml_model = Noneml_anlysis = None

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

    "current_round": {
        "course": handicap_round1["course"],
        "date": handicap_round1["date"],
        "scores": handicap_round1["holes"],
        "pars": handicap_round1["pars"],
        "total_score": sum(
            handicap_round1["holes"]
        ),
        "course_par": handicap_round1["par"],
        "course_rating":
            handicap_round1["course_rating"],
        "slope_rating":
            handicap_round1["slope_rating"],
        "pcc": handicap_round1["pcc"]
    },

    "strokes_gained":
        strokes_gained_data,
    "ml_analysis":
        ml_analysis
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
        "\nAsk me a golf question! "
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
