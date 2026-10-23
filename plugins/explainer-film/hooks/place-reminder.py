"""What this does: runs each time the person sends a message (a UserPromptSubmit hook of the explainer-film plugin). When the message is about BUILDING a place, a set or props in 3D (a
village, a harbour, a mine, a barn, a room, a prop, Blender itself), it prints a three-line reminder (the last line also names the card-time and batch rule), which Claude Code adds to what the model reads: such work goes through the
surface-and-wear pass and the construction check, even when the message names neither; its second line also sends a place that will be shown in the film to the
skill build-and-paint-a-place and the tips guide before a camera is placed (a film view is 1080 x 1920). For any other message it prints nothing and costs nothing.
The person's own words win: a message that says not to use the plugin or its skills ("plain Blender", "without the plugin", "do not use the plugin",
"don't use the plugin", "do not use the skill") gets nothing, even when it is about building a place (the person tests ideas with and without the plugin).
Those words are read narrowly: "with and without the plugin" (a comparison) still gets the reminder, and so does "do not use skills from another set" (a skill
named after "skills" is some other skill; only "the skill(s)" ending the phrase, or this plugin's skills, leave the plugin out).
Why it exists: the plugin's skills are picked by their descriptions, and other skills (a general Blender skill, for example) compete for the same request. This reminder names the plugin's
skill and the commands in the one place a model cannot miss, the start of its turn.
It reads the message from the JSON Claude Code sends on standard input ({"prompt": "..."}); a message it cannot read gets no reminder, and it always exits 0 (a hook must never stop the person's work).
Needs only Python 3 (standard library). Plain words, no keys, no settings.
A concrete example: "Build a canal lock with a brick wall and a wooden gate" gets the reminder, and so do "Build an old railway station for a film" and "Make a fish market by the sea";
"what is the weather in Oslo", "fix the typo in my README", "make a market analysis" and "Build a canal lock in plain Blender, do not use the plugin" get nothing.
"""
import json
import re
import sys

# the words are ordinary names of places, buildings and props, chosen so that ordinary code and film talk does not match ("add a cart to the shop", "build a random forest", "make room for",
# "make the build stable", "the film's scene" do not): a word that is also common in software talk is left out
BUILD_WORDS = r'build|building|built|make|making|create|creating|design|construct|assemble|put together|generate|populate|dress|furnish'
PLACE_WORDS = (r'village|hamlet|harbou?r|quay|canal|quarry|farm|barn|cabin|hut|house|castle|ruins?|tower|temple|church|windmill|watermill|mill|courtyard|yard|garden|'
               r'jungle|island|cave|dungeon|tavern|inn|warehouse|diorama|landscape|town|city|alley|interior|kitchen|bedroom|cellar|attic|props?|furniture|barrel|crate|wagon|'
               r'fence|coal mine|a mine|the mine|mine yard|mine shaft|'
               # streets, railways, markets and the water's edge (a market or a station only with a word that makes it a place: "market research" and "work station" stay silent)
               r'street(?! address)|railway|(?:railway|train|bus|tram|petrol|gas|fire|police|pumping|weather|lifeboat|signal) station|station (?:building|yard|platform|house)|'
               r'(?:fish|street|flower|cattle|covered|night|meat|fruit|food|town|village|old) market|market (?:square|hall|stalls?|street|place|cross)|pier|wharf|chapel|'
               # buildings of faith, defence and great houses, workplaces and yards (fix round): "bridge" and "factory" only as a place ("bridge pattern" and "factory function" stay silent),
               # a lighthouse not when it is the web tool's score, a shed not when it sheds something
               r'monastery|abbey|cloister|convent|shrine|pagoda|mosque|cathedral|lighthouse(?! (?:score|report|audit|ci))|fort|fortress|palace|manor|cottage|gatehouse|'
               r'classroom|bakery|brewery|foundry|sawmill|kiln|granary|shed(?! (?:light|some|load|weight|its|their))|shipyard|docks|bazaar|plaza|'
               r'factory (?:floor|yard|building|hall)|(?:stone|foot|rope|wooden|timber|iron|brick|railway|canal) bridge|bridge over')
ALWAYS_WORDS = r'blender|bpy|3d|three-d|\.blend'
# the person's "leave the plugin out" (it wins over the reminder): plain Blender, without the plugin, do not / don't / never use the plugin or its skills.
# Read narrowly: "with and without the plugin" is a comparison, not a leave-out; "do not use skills from X" or "do not use the skill NAME" is about some other skill,
# so a bare "skill(s)" leaves the plugin out only when the phrase ends there (or goes on with "at all", "here", "of this plugin" ...)
NOT_USE = r"(?:do not|don't|dont|don\u2019t|never|not to) use "
LEAVE_OUT_WORDS = (r"plain blender|(?<!with and )(?<!with or )without (?:the |this |any )?(?:explainer-film )?plugin|"
                   + NOT_USE + r"(?:the |this |any )?(?:explainer-film )?plugin|"
                   + NOT_USE + r"(?:the |this |any |its )?(?:explainer-film |(?:the |this )?plugin(?:'s|\u2019s)? )skills?|"
                   + NOT_USE + r"(?:the |this |any |its |these )?skills?(?= *(?:$|[.,;:!?)]|at all|here|and |or |of (?:the |this )?plugin|from (?:the |this )?plugin|for (?:this|it)))")

REMINDER = (
    'explainer-film reminder (ignore it if this is not 3D work): a place, a set or props built in Blender go through the surface-and-wear pass and the construction check, even when the '
    'request names neither (real normal maps and displacement, dirt, grime, weeds, moss, weathering, damage, wetness, parts that are carried and at real size).\n'
    'Read the skill surfaces-wear-and-construction first (its first screen has the steps), then run: explainer-film-place finish, explainer-film-place audit, explainer-film-preflight place. '
    'If the place will be shown in the film (on a phone), also read the skill build-and-paint-a-place and sections 4 to 12 of kit/docs/LLM tips and tricks.md before you place a camera; '
    'a film view is 1080 x 1920, not 1200 x 800.\n'
    'Nothing is drawn, rendered or painted until the preflight place stage passes; report what was measured, what was only judged and what failed. Rented-card time is limited: make every change in ONE sweep, then look once; '
    'try a change as about 10 far-apart variations in ONE batch (explainer-film-place variations), small quick pictures until the end, full-size pictures once at the very end, and report your card seconds.'
)


def says_leave_the_plugin_out(text):
    """True when the person's message says not to use the plugin or its skills: their words win, so no reminder is printed."""
    lowered = re.sub(r'\s+', ' ', text.lower())
    return bool(re.search(r'(?<![a-z])(' + LEAVE_OUT_WORDS + r')(?![a-z])', lowered))


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
    if isinstance(prompt, str) and is_about_building_a_place(prompt) and not says_leave_the_plugin_out(prompt):
        print(REMINDER)
    return 0


if __name__ == '__main__':
    sys.exit(main())
