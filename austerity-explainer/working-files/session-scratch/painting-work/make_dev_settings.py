# makes a development copy of the plugin's film-settings.json with the painting_tools section added (scratch only)
import json, sys
real='/home/user/Music/plugins/explainer-film/kit/film-settings.json'
d=json.load(open(real))
d['painting_tools']=json.load(open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/painting-work/my-section.json'))
json.dump(d,open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/painting-work/film-settings-dev.json','w'),indent=1)
print('ok', len(d))
