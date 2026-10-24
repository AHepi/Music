from PIL import Image
import sys
base='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/'
for name in ['composed-end.png','composed-end-2.png']:
    im=Image.open(base+name).convert('RGB')
    tag=name.replace('.png','')
    # bottom-left quarter, side by side later
    im.crop((0,1300,700,1920)).save(f'{tag}-bl.png')
    im.crop((520,1150,1080,1650)).resize((840,750)).save(f'{tag}-group.png')
    im.crop((680,740,820,920)).resize((420,540),Image.NEAREST).save(f'{tag}-vp.png')
    im.crop((0,900,320,1150)).resize((640,500)).save(f'{tag}-cart.png')
    im.crop((700,150,1080,650)).save(f'{tag}-lamp.png')
