"""What this does: runs each time the person sends a message (a UserPromptSubmit hook of the explainer-film plugin). When the message is about BUILDING a place, a set or props in 3D (a
village, a harbour, a mine, a barn, a room, a prop, Blender itself), it prints a three-line reminder (the last line also names the card-time and batch rule), which Claude Code adds to what the model reads: such work goes through the
surface-and-wear pass and the construction check, even when the message names neither. For any other message it prints nothing and costs nothing.
Why it exists: the plugin's skills are picked by their descriptions, and other skills (a general Blender skill, for example) compete for the same request. This reminder names the plugin's
skill and the commands in the one place a model cannot miss, the start of its turn.
It reads the message from the JSON Claude Code sends on standard input ({"prompt": "..."}); a message it cannot read gets no reminder, and it always exits 0 (a hook must never stop the person's work).
Needs only Python 3 (standard library). Plain words, no keys, no settings.
A concrete example: "Build a canal lock with a brick wall and a wooden gate" gets the reminder; "what is the weather in Oslo" and "fix the typo in my README" get nothing.
"""
import json
import re
import sys

# the words are ordinary names of places, buildings and props, chosen so that ordinary code and film talk does not match ("add a cart to the shop", "build a random forest", "make room for",
# "make the build stable", "the film's scene" do not): a word that is also common in software talk is left out
BUILD_WORDS = r'build|building|built|make|making|create|creating|design|construct|assemble|put together|generate|populate|dress|furnish'
PLACE_WORDS = (r'village|hamlet|harbou?r|quay|canal|quarry|farm|barn|cabin|hut|house|castle|ruins?|tower|temple|church|windmill|watermill|mill|courtyard|yard|garden|'
               r'jungle|island|cave|dungeon|tavern|inn|warehouse|diorama|landscape|town|city|alley|interior|kitchen|bedroom|cellar|attic|props?|furniture|barrel|crate|wagon|'
               r'fence|coal mine|a mine|the mine|mine yard|mine shaft')
ALWAYS_WORDS = r'blender|bpy|3d|three-d|\.blend'

REMINDER = (
    'explainer-film reminder (ignore it if this is not 3D work): a place, a set or props built in Blender go through the surface-and-wear pass and the construction check, even when the '
    'request names neither (real normal maps and displacement, dirt, grime, weeds, moss, weathering, damage, wetness, parts that are carried and at real size).\n'
    'Read the skill surfaces-wear-and-construction first (its first screen has the steps), then run: explainer-film-place finish, explainer-film-place audit, explainer-film-preflight place.\n'
    'Nothing is drawn, rendered or painted until the preflight place stage passes; report what was measured, what was only judged and what failed. Rented-card time is limited: make every change in ONE sweep, then look once; '
    'try a change as about 10 far-apart versions in ONE batch (explainer-film-place variations), small quick pictures until the end, full-size pictures once at the very end, and report your card seconds.'
)


def is_about_building_a_place(text):
    lowered = ' ' + re.sub(r'\s+', ' ', text.lower()) + ' '
    if re.search(r'(?<![a-z0-9])(' + ALWAYS_WORDS + r')(?![a-z0-9])', lowered):
        return True
    builds = re.search(r'(?<![a-z])(' + BUILD_WORDS + r')(?![a-z])', lowered)
    place = re.search(r'(?<![a-z])(' + PLACE_WORDS + r')(?![a-z])', lowered)
    return bool(builds and place)


def main():
    try:
        data = json.load(sys.stdin)
        prompt = data.get('prompt') if isinstance(data, dict) else None
    except (ValueError, OSError):
        return 0
    if isinstance(prompt, str) and is_about_building_a_place(prompt):
        print(REMINDER)
    return 0


if __name__ == '__main__':
    sys.exit(main())
