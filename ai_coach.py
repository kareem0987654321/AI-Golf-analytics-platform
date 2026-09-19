from openai import OpenAI


client = OpenAI()


def analyze_player(player_data):

    sg_data = player_data["strokes_gained"]

    if sg_data is None:

        return {
            "strongest_area": None,
            "strongest_value": None,
            "weakest_area": None,
            "weakest_value": None
        }

    averages = sg_data["averages"]

    if averages is None:

        return {
            "strongest_area": None,
            "strongest_value": None,
            "weakest_area": None,
            "weakest_value": None
        }

    categories = {
        "off_the_tee": averages["off_the_tee"],
        "approach": averages["approach"],
        "around_the_green": averages["around_the_green"],
        "putting": averages["putting"]
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
        "strongest_area": strongest_category,
        "strongest_value": categories[strongest_category],
        "weakest_area": weakest_category,
        "weakest_value": categories[weakest_category]
    }


def create_ai_context(
    player_data,
    analysis
):

    current_round = player_data["current_round"]

    context = f"""
You are an AI golf performance coach.

Player:
{player_data['name']}

Handicap Index:
{player_data['handicap']['index']}

Low Handicap:
{player_data['handicap']['low_handicap']}

CURRENT ROUND:

Course:
{current_round['course']}

Date:
{current_round['date']}

Total Score:
{current_round['total_score']}

Course Par:
{current_round['course_par']}

Score Relative to Par:
{current_round['total_score'] - current_round['course_par']:+d}

Course Rating:
{current_round['course_rating']}

Slope Rating:
{current_round['slope_rating']}

PCC:
{current_round['pcc']}

Hole-by-Hole Scores:
{current_round['scores']}

Hole-by-Hole Pars:
{current_round['pars']}
"""

    if player_data["strokes_gained"] is None:

        context += """

STROKES GAINED:

The player did not provide shot-by-shot
Strokes Gained data for this round.

Analyze the round using the available score,
course difficulty, handicap, and hole-by-hole
scoring information.

Do not invent Strokes Gained statistics.

Do not claim that course, score, handicap,
or hole-by-hole information is missing when
it is provided above.
"""

    else:

        averages = (
            player_data["strokes_gained"]["averages"]
        )

        context += f"""

AVERAGE STROKES GAINED:

Off the Tee:
{averages['off_the_tee']:.2f}

Approach:
{averages['approach']:.2f}

Around the Green:
{averages['around_the_green']:.2f}

Putting:
{averages['putting']:.2f}
"""

        if analysis["strongest_area"] is not None:

            context += f"""

Strongest Area:
{analysis['strongest_area']}
({analysis['strongest_value']:.2f})

Weakest Area:
{analysis['weakest_area']}
({analysis['weakest_value']:.2f})
"""

    ml_analysis = player_data.get(
        "ml_analysis"
    )

    if ml_analysis is not None:

        most_common = (
            ml_analysis["most_common_pattern"]
        )

        context += f"""

MACHINE LEARNING PERFORMANCE ANALYSIS:

A K-Means clustering model analyzed the player's
historical Strokes Gained rounds and identified
recurring performance patterns.

Most Common Pattern:
Pattern {most_common['pattern_number']}

Frequency:
{most_common['round_count']} rounds
({most_common['percentage']:.1f}%)

Average Strokes Gained profile for this pattern:

Off the Tee:
{most_common['off_the_tee']:.2f}

Approach:
{most_common['approach']:.2f}

Around the Green:
{most_common['around_the_green']:.2f}

Putting:
{most_common['putting']:.2f}

Strongest Area:
{most_common['strongest_area']}
({most_common['strongest_value']:.2f})

Weakest Area:
{most_common['weakest_area']}
({most_common['weakest_value']:.2f})

Use this machine-learning analysis when discussing
recurring performance tendencies.

Clearly distinguish recurring historical patterns
from the player's performance in the current round.

Do not invent patterns that are not supported by
the provided machine-learning results.
"""

    else:

        context += """

MACHINE LEARNING PERFORMANCE ANALYSIS:

There are not yet enough historical Strokes Gained
rounds to identify recurring performance patterns.
"""

    return context


def get_initial_ai_analysis(ai_context):

    response = client.responses.create(
        model="gpt-5.6",
        input=ai_context
    )

    return response.output_text


def ask_ai(
    ai_context,
    user_question,
    conversation_history
):

    conversation_text = ""

    for message in conversation_history:

        conversation_text += (
            f"{message['role']}: "
            f"{message['content']}\n"
        )

    response = client.responses.create(
        model="gpt-5.6",
        input=f"""
You are an AI golf performance coach.

Use the player's golf data below to answer
the player's question.

PLAYER DATA:

{ai_context}

PREVIOUS CONVERSATION:

{conversation_text}

PLAYER QUESTION:

{user_question}

Structure your response using these sections:

1. Strengths
Identify what the player is doing well based
on the available data.

2. Weakness
Identify an important area that could be
improved based on the available data.

3. Analysis
Explain what the available data suggests.

4. Practice Recommendation
Give 2-3 specific practice ideas the player
can use.

Use only the statistics that are actually
provided.
Do not invent Strokes Gained statistics.
"""
    )

    return response.output_text
