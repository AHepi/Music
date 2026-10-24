"""Checks every --flag written after a calculator command in the plugin's docs is one that tool accepts."""
import glob, os, re, subprocess, sys
root = sys.argv[1]
kit = os.path.join(root, 'kit')
files = [os.path.join(root, 'README.md'), os.path.join(kit, 'docs', 'LLM tips and tricks.md')] + glob.glob(os.path.join(root, 'skills', '*', '*.md'))
tools = {'calculators/frame_geometry.py', 'calculators/place_facts.py', 'calculators/plan_shot.py', 'calculators/view_audit.py',
         'calculators/paint_request.py', 'calculators/after_painting.py', 'calculators/plan_states.py', 'calculators/plan_page_timing.py',
         'calculators/plan_budget.py', 'calculators/plan_effects.py', 'calculators/plan_lights.py', 'calculators/settings.py',
         'narration-tools/lint_script.py', 'narration-tools/sound_gates.py', 'paper-film/tools/camera_audit.py',
         'paper-film/blender/model_lint.py', 'paper-film/blender/make_check_file.py'}
short = {os.path.basename(t)[:-3]: t for t in tools}
helps = {}
def help_of(tool, sub):
    key = (tool, sub)
    if key not in helps:
        args = ['python3', '-I', '-B', os.path.join(kit, tool)] + ([sub] if sub else []) + ['--help']
        helps[key] = subprocess.run(args, capture_output=True, text=True).stdout
    return helps[key]
problems, checked = [], 0
for f in files:
    text = open(f, encoding='utf-8').read()
    for chunk in re.findall(r'`([^`]+)`', text):
        m = re.search(r'((?:calculators|narration-tools|paper-film/tools|paper-film/blender)/\w+\.py|\b(?:' + '|'.join(short) + r')\.py)\s+(.*)', chunk)
        if not m: continue
        tool = m.group(1)
        tool = tool if '/' in tool else short[tool[:-3]]
        if tool not in tools: continue
        rest = m.group(2)
        words = rest.split()
        sub = words[0] if words and re.match(r'^[a-z][a-z-]+$', words[0]) and not words[0].startswith('-') else None
        top = help_of(tool, None)
        if sub and not re.search(r'\{[^}]*\b' + re.escape(sub) + r'\b', top):
            if tool.endswith('settings.py') and sub in ('show','get','check','sections','profile'):
                pass
            else:
                sub = None
        h = help_of(tool, sub) if sub else top
        for flag in re.findall(r'(?<![\w-])(--[a-z][a-z-]*)', rest):
            if flag in ('--',): continue
            checked += 1
            if flag not in h and not (tool.endswith('make_check_file.py') or tool.endswith('model_lint.py')) or (flag not in h):
                problems.append((os.path.relpath(f, root), tool, sub, flag))
print(checked, 'flags checked;', len(problems), 'not found in the tool\'s help')
for p in problems: print('  ', p)
