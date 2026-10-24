"""What this does: asks the place kit's own role guesser (roles.hint_role, plain Python, no Blender) what role it would give
to plain names a railway-station or fish-harbour builder might use, so the judge can check the newcomer's claims. Writes nothing."""
import json, sys
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit import roles
table = json.load(open('/home/user/Music/plugins/explainer-film/kit/place-kit/data/roles.json'))
names = ["Rail 1", "Railway track", "Canopy column", "Water tower", "Water crane", "Station roof slate", "Station building walls",
         "Platform", "Sleeper", "Crane", "Footbridge", "Buffer stop", "Loading dock", "Weighbridge",
         "Fish box", "Fish market counter", "Market stall", "Jetty plank", "Jetty pile", "Bollard", "Quay wall", "Quay coping",
         "Mooring ring", "Net", "Float", "Lobster pot", "Fish", "Ice", "Slipway", "Boat hull", "Mast"]
for name in names:
    print(f"{name!r:28} -> {roles.hint_role(table, {'name': name})}")
for coll in ["Place: track_and_signals", "Place: goods_yard", "Place: rails_and_signals", "Place: permanent_way", "Place: freight_shed", "Place: furnishings", "Place: platforms",
             "Place: market", "Place: jetty", "Place: quay", "Place: boats", "Place: props"]:
    print(f"Object.012 in {coll!r:28} -> {roles.hint_role(table, {'name': 'Object.012', 'collections': [coll]})}")
