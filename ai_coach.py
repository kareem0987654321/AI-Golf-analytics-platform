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

    context = f"""
You are an AI golf performance coach.

Player:
{player_data['name']}

Handicap Index:
{player_data['handicap']['index']}

Low Handicap:
{player_data['handicap']['low_handicap']}
"""

    if player_data["strokes_gained"] is None:

        context += """

Strokes Gained:

The player did not provide shot-by-shot
Strokes Gained data for this round.

Use the available handicap and score
information for your analysis.

Do not invent Strokes Gained statistics.
"""

    else:

        averages = (
            player_data["strokes_gained"]["averages"]
        )

        context += f"""

Average Strokes Gained:

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