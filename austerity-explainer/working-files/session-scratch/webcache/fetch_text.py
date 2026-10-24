# helper: fetch a URL, strip html, print text (first N chars) plus Last-Modified header
import sys, re, html, urllib.request, ssl, os
url=sys.argv[1]; start=int(sys.argv[2]) if len(sys.argv)>2 else 0; n=int(sys.argv[3]) if len(sys.argv)>3 else 6000
import subprocess
out=subprocess.run(['curl','-sSL','-m','40','-D','-','-A','Mozilla/5.0',url],capture_output=True)
raw=out.stdout.decode('utf8','ignore')
head,_,body=raw.partition('\r\n\r\n')
# curl -D - with -L prints multiple header blocks; take the last
parts=raw.split('\r\n\r\n')
hdrs=[p for p in parts if p.startswith('HTTP/')]
lm=[l for l in (hdrs[-1].split('\r\n') if hdrs else []) if l.lower().startswith(('last-modified','date','content-type'))]
body=raw[len(''.join(p+'\r\n\r\n' for p in hdrs)):] if hdrs else raw
t=re.sub(r'<script.*?</script>','',body,flags=re.S); t=re.sub(r'<style.*?</style>','',t,flags=re.S)
t=re.sub(r'<[^>]+>','\n',t); t=html.unescape(t); t=re.sub(r'[ \t]+',' ',t); t=re.sub(r'\n\s*\n+','\n',t)
print('HEADERS:',lm); print('LEN',len(t)); print(t[start:start+n])
