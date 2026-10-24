"""Plain note: pull single frames out of the round 5 film of pages 3 to 5.
Give chapter times in seconds; each is saved as fr/t-<seconds>.png (1080 x 1920).
The film starts at chapter frame 1421, 30 frames a second."""
import subprocess, sys, os
film = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round5-film/film/pages-3-to-5-silent.mp4"
out = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/check-round-5/fr"
times = [float(x) for x in sys.argv[1:]]
idx = [round(t * 30) - 1421 for t in times]
sel = "+".join(f"eq(n\\,{i})" for i in idx)
tmp = os.path.join(out, "tmp-%03d.png")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", film, "-vf", f"select='{sel}'", "-vsync", "0", tmp], check=True)
order = sorted(range(len(idx)), key=lambda k: idx[k])
for n, k in enumerate(order):
    os.replace(os.path.join(out, f"tmp-{n+1:03d}.png"), os.path.join(out, f"t-{times[k]:.2f}.png"))
print("saved", len(idx))
