import json,sys,urllib.request,time
ids=sys.argv[1:]
out={}
for i in ids:
    try:
        req=urllib.request.Request('https://api.polyhaven.com/files/'+i,headers={'User-Agent':'Mozilla/5.0 (texture-research)'})
        f=json.load(urllib.request.urlopen(req,timeout=30))
        maps=sorted(f.keys())
        def size(m,res='2k',fmt='jpg'):
            try:
                x=f[m][res][fmt]; return x.get('size')
            except Exception: return None
        out[i]={'maps':maps,'diff2k_kb':(size('Diffuse')or 0)//1024,'rough2k_kb':(size('Rough')or 0)//1024,'nor2k_kb':(size('nor_gl','2k','jpg') or size('nor_gl','2k','png') or 0)//1024,'disp2k_kb':(size('Displacement','2k','png') or size('Displacement','2k','jpg') or 0)//1024,'res':sorted(f['Diffuse'].keys()) if 'Diffuse' in f else None}
    except Exception as e:
        out[i]={'err':str(e)}
    time.sleep(0.3)
json.dump(out,open('files_info.json','w'),indent=1)
for k,v in out.items(): print(k,v)
