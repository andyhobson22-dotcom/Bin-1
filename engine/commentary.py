"""Text commentary generator for match events."""
import random

TEMPLATES = {
    'phase': {
        'gain': [
            "{player} carries strongly for {team}, breaking through the gainline!",
            "{team} move the ball wide, {player} makes good metres!",
            "Quick hands from {team}, {player} finds a gap and surges forward!",
            "{player} picks and goes from the ruck, {team} making ground in the {zone}.",
            "Lovely offload from {player}! {team} are rolling forward now.",
            "{team} shift it left, then right — {player} exploits the overlap!",
        ],
        'neutral': [
            "{player} takes it into contact for {team}. Recycled, but no real ground gained.",
            "{team} go through the phases in the {zone}. {player} held up at the gainline.",
            "Pick and go from {player}. {team} retain possession but it's slow ball.",
            "{team} keep patient possession. {player} crashes it up but the defence holds firm.",
        ],
        'turnover': [
            "{player} is isolated at the ruck! {team} lose possession.",
            "Knock-on by {player}! {team} spill the ball under pressure.",
            "The defence swarms {player}, forcing the error. {team} have lost it.",
            "Handling error from {player}! The ball goes to ground.",
        ],
    },
    'scrum': {
        'won': [
            "{team} win clean ball from the scrum in the {zone}.",
            "Solid scrum from {team}. The ball is out and away.",
            "{team}'s pack gets a good shove on, clean ball for the backs.",
        ],
        'lost': [
            "{team}'s scrum is disrupted! The opposition win the ball against the head!",
            "Messy scrum — {team} lose their own put-in!",
        ],
        'penalty_won': [
            "Huge scrum from {team}! The opposition pack collapses — penalty!",
            "{team} demolish the opposition scrum! Penalty advantage.",
        ],
        'penalty_against': [
            "{team}'s scrum goes wrong. The referee penalises them for collapsing.",
            "The scrum wheels illegally. Penalty against {team}.",
        ],
    },
    'lineout': {
        'won': [
            "{team} secure their own lineout in the {zone}.",
            "Clean catch at the lineout for {team}. Well executed.",
            "{team}'s lineout functions well — they have possession.",
        ],
        'lost': [
            "{team}'s lineout throw goes astray! Opposition steal!",
            "The jumper can't reach it — {team} lose their lineout.",
        ],
        'penalty_won': [
            "{team} win the lineout and the opposition are penalised for not rolling away.",
            "Lineout won by {team} and they set up a driving maul — penalty advantage!",
        ],
        'penalty_against': [
            "Not straight at the lineout. Penalty against {team}.",
            "{team}'s throw is crooked. Free kick to the opposition.",
        ],
    },
    'try': [
        "TRY! {scorer} touches down for {team}! Brilliant finish!",
        "TRY! {scorer} crashes over the line for {team}!",
        "TRY! {team} score through {scorer}! What a moment!",
        "TRY! {scorer} dives over in the corner! {team} are celebrating!",
        "TRY! Excellent team move and {scorer} finishes it off for {team}!",
        "TRY! {scorer} powers through the last defender! {team} score!",
    ],
    'held_up': [
        "{player} is held up over the line! {team} so close but no try.",
        "Held up! {player} gets there for {team} but can't ground it.",
    ],
    'try_saved': [
        "Incredible last-ditch tackle by {defender}! Try denied!",
        "{defender} gets back to make a try-saving tackle! What a defensive effort!",
        "Scramble defence! {defender} just manages to drag the attacker into touch.",
    ],
    'conversion_good': [
        "{kicker} steps up... and it's GOOD! Conversion for {team}!",
        "Right between the posts! {kicker} adds the extras.",
        "{kicker} makes no mistake with the conversion.",
    ],
    'conversion_missed': [
        "{kicker} lines up the conversion... it drifts wide. No good.",
        "The conversion is missed by {kicker}. Just off target.",
    ],
    'penalty_awarded': [
        "Penalty to {team}! {offender} from {offending_team} is penalised in the {zone}.",
        "The referee blows for a penalty. {offending_team}'s {offender} infringed.",
        "Penalty! {offending_team} give away a free kick. {team} have a chance here.",
    ],
    'penalty_kick_good': [
        "{kicker} with the penalty kick... GOOD! Three points for {team}!",
        "Straight through the posts! {kicker} slots the penalty for {team}.",
        "{kicker} makes it look easy. Penalty goal for {team}!",
    ],
    'penalty_kick_missed': [
        "{kicker} strikes the penalty... it slides wide! No score.",
        "Missed! {kicker}'s penalty drifts off target.",
    ],
    'drop_goal_good': [
        "DROP GOAL! {kicker} nails it for {team}! Three points!",
        "{kicker} drops for goal... IT'S OVER! Brilliant drop goal for {team}!",
    ],
    'drop_goal_missed': [
        "{kicker} attempts the drop goal... it falls short. Not this time.",
        "Drop goal attempt from {kicker}... it goes wide. No score.",
    ],
    'kick_good': [
        "{kicker} puts in a lovely kick for {team}. Great territory gained.",
        "Superb boot from {kicker}! {team} find touch deep in opposition territory.",
        "{kicker} hoists it high. {team} chase well and pin the opposition back.",
    ],
    'kick_poor': [
        "{kicker}'s kick doesn't find touch for {team}. Poor execution.",
        "Aimless kick from {kicker}. The opposition gather easily and counter.",
    ],
    'turnover': [
        "{player} wins a crucial turnover for {team} at the breakdown!",
        "Turnover! {player} jackals brilliantly and {team} have the ball.",
        "{attacking_team} lose possession! {player} rips it away for {team}.",
        "The referee awards a turnover. {player} was strong over the ball for {team}.",
    ],
    'yellow_card': [
        "YELLOW CARD! {player} from {team} is sent to the sin bin!",
        "The referee reaches for yellow! {player} of {team} must spend 10 minutes off the field.",
        "That's a yellow card for {player}! {team} are down to 14 men.",
    ],
    'red_card': [
        "RED CARD! {player} from {team} is sent off! That's a game-changer!",
        "Straight red for {player}! {team} will play the rest of the match with 14 men.",
    ],
}


def generate_commentary(event_type, context):
    """Generate commentary text for a match event.

    Args:
        event_type: Type of event (e.g., 'try', 'scrum', 'phase')
        context: Dict with variables to fill into template

    Returns:
        Commentary string
    """
    templates = TEMPLATES.get(event_type, None)

    if templates is None:
        return f"Play continues..."

    # Some event types have sub-outcomes
    if isinstance(templates, dict):
        outcome = context.get('result', 'neutral')
        templates = templates.get(outcome, ["Play continues in the {zone}."])

    template = random.choice(templates)

    try:
        return template.format(**context)
    except KeyError:
        return template
