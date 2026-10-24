import sys, json
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
sys.dont_write_bytecode = True
from place_kit import roles as R
table = json.load(open('/home/user/Music/plugins/explainer-film/kit/place-kit/data/roles.json'))
names = ['Rail 1','Railway track','Sleeper 12','Ballast','Ballast gravel','Platform','Platform edge coping','Platform paving','Station building walls','Station roof slate','Canopy girder','Canopy column','Signal post','Signal arm','Water tower','Water crane','Goods shed walls','Goods shed door','Loading dock','Yard cobbles','Yard ground','Wagon 1','Wagon wheel','Buffer stop','Crane','Footbridge','Platform lamp','Bench','Trolley','Milk churn','Sack','Weighbridge','Point lever','Station clock','Fence','Gate','Chimney','Station sign','Name board','Crate','Barrel','Retaining wall','Embankment','Cattle dock','Coal stage','Coal heap','Telegraph pole','Stationmaster office','Waiting room floor','Ticket office window']
for n in names:
    obj = {'name': n, 'collections': [], 'materials': []}
    try:
        r = R.hint_role(table, obj)
    except Exception as e:
        r = 'ERR %s' % e
    print('%-24s -> %s' % (n, r))
