import hashlib, sys, subprocess, urllib.parse, os, time
# usage: python3 -I _getcommons.py "File name.jpg" [width]
name = sys.argv[1].replace(" ", "_")
width = int(sys.argv[2]) if len(sys.argv) > 2 else 960
h = hashlib.md5(name.encode()).hexdigest()
q = urllib.parse.quote(name)
base = f"https://upload.wikimedia.org/wikipedia/commons"
url = f"{base}/thumb/{h[0]}/{h[:2]}/{q}/{width}px-{q}"
out = os.path.join("_raw/photos", name[:60].replace("/", "_"))
r = subprocess.run(["curl","-sS","-m","60","-L","-A","ReferenceStudyBot/1.0 (personal film research)","-o",out,"-w","%{http_code} %{size_download}",url],capture_output=True,text=True)
print(url, r.stdout, r.stderr[:200])
