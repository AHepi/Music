import urllib.request,sys,os
ids=sys.argv[1:]
for i in ids:
    p='thumbs/%s.png'%i
    if os.path.exists(p): continue
    try:
        req=urllib.request.Request('https://cdn.polyhaven.com/asset_img/thumbs/%s.png?width=256&height=256'%i,headers={'User-Agent':'Mozilla/5.0 (texture-research)'})
        open(p,'wb').write(urllib.request.urlopen(req,timeout=30).read())
    except Exception as e: print('fail',i,e)
