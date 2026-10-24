import sys, os, tarfile, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
import rr
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/reuse_proof/remote_out/entry'
rr.sync()
rr.run(f'rm -rf "{OUT}" && mkdir -p "{OUT}"', limit=120)
cmd = f'"{rr.BLENDER}" -b --disable-autoexec "{rr.SCENE}" --python "{rr.KIT}/harness/test_weathering_entry.py" -- japanese_courtyard mossy_courtyard_rough "{OUT}/entry_test.json" photo A 600 400 16 > "{OUT}/run.log" 2>&1'
code, tail = rr.run(cmd, limit=1500)
print('code', code)
tar_remote = OUT + '.tar'
rr.run(f'cd "{OUT}" && rm -rf entry_test_pictures/*.png.tmp; tar -cf "{tar_remote}" entry_test.json run.log && ls | wc -l', limit=300)
lt = os.path.join(tempfile.gettempdir(), 'entry.tar')
rr.client('download', tar_remote, '--local', lt, timeout=600)
os.makedirs(OUT, exist_ok=True)
with tarfile.open(lt) as a:
    a.extractall(OUT)
os.remove(lt)
rr.run(f'rm -rf "{OUT}/entry_test_pictures" "{tar_remote}"', limit=120)
print(open(OUT + '/entry_test.json').read()[:4000])
