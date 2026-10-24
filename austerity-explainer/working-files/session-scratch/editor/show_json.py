# Prints a JSON file as an indented outline (long values cut short). Usage: python3 -I show_json.py FILE [MAXLEN]
import json, sys
d = json.load(open(sys.argv[1]))
maxlen = int(sys.argv[2]) if len(sys.argv) > 2 else 200
def show(o, ind=0):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)) and not (isinstance(v, list) and all(not isinstance(x, (dict, list)) for x in v) and len(str(v)) < 120):
                print(' ' * ind + str(k) + ':'); show(v, ind + 2)
            else:
                s = str(v); print(' ' * ind + str(k) + ': ' + (s if len(s) < maxlen else s[:maxlen] + '...'))
    elif isinstance(o, list):
        for v in o:
            if isinstance(v, (dict, list)):
                print(' ' * ind + '-'); show(v, ind + 2)
            else:
                s = str(v); print(' ' * ind + '- ' + (s if len(s) < maxlen else s[:maxlen] + '...'))
show(d)
