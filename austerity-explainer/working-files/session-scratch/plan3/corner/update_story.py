# Updates the project story for log 32: appends the log entry, refreshes "Where things stand", the spending line
# and the next step. Run once, after RECHECK in the draft is filled in.
import sys

story = '/home/user/Music/austerity-explainer/project-notes/Austerity explainer - project story.md'
draft = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/log32-draft.md'
s = open(story).read()
entry = open(draft).read().rstrip('\n')
assert 'RECHECK' not in entry, 'fill in RECHECK first'
assert '\n32. **' not in s, 'log 32 is already in the story'


def swap(old, new):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new, 1)


# the log entry goes after log 31, before "## Next step"
swap('\n## Next step\n', '\n' + entry + '\n\n## Next step\n')
# where things stand: a new first bullet
swap('## Where things stand\n\n', '''## Where things stand

- **The notice corner, painted and filmed** (log 32): "32 Test - notice corner slide" (13 seconds, music only).
  The picture you liked, rebuilt in our street with our props, fixed after three rounds of critics, painted
  in the series' style and filmed as one slow slide toward the notice without turning. Checked in motion by
  helpers; the one fault they found (the fire's shadows fading off the pavement) is fixed. The shot checker
  passes 32 of 38 checks on the finished still, and on the film's own end frame the notice is lit from below
  and the frame is balanced. Waiting for your view.
''')
swap('- Spent so far: about US$10.30 in all (log 31 spent nothing):',
     '- Spent so far: about US$10.60 in all (log 32: about 20 to 45 US cents for two paintings; log 31 spent nothing):')
swap('of its 36 checks. Not painted or filmed yet.', 'of its 36 checks. Painted and filmed in log 32 (above).')
# the next step
i = s.index('## Next step\n')
j = s.index('\n## Traps', i)
s = s[:i] + '''## Next step

Watch "32 Test - notice corner slide" on your phone and say whether this look and composition is the one to
build the next shots on. If it is, the next improvement would be the notice's key lines, which are only just
readable on a phone.
''' + s[j:]
open(story, 'w').write(s)
print('story updated')
