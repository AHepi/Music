# Marks the brightest 5% of one prop's visible pixels in magenta and saves a crop round the prop.
import sys, types, numpy as np, cv2
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
import check_shot
args = types.SimpleNamespace(check='/home/user/work/paper-pop-up-film-kit/examples/notice-corner/shot-check.json', facts=sys.argv[1], picture=sys.argv[2],
                             out='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/outline-shift', title='', render_log=None)
shot = check_shot.Shot(args)
g = sys.argv[3]
mask = shot.visible[g]
limit = np.percentile(shot.grey[mask], 95)
hot = mask & (shot.grey >= limit)
drawn = shot.picture.copy()
drawn[hot] = (255, 0, 255)
ys, xs = np.nonzero(mask)
crop = np.hstack([shot.picture, drawn])[max(0, ys.min() - 20):ys.max() + 20]
crop = np.hstack([shot.picture[max(0, ys.min() - 20):ys.max() + 20, max(0, xs.min() - 20):xs.max() + 20],
                  drawn[max(0, ys.min() - 20):ys.max() + 20, max(0, xs.min() - 20):xs.max() + 20]])
cv2.imwrite(sys.argv[4], crop)
print(g, 'brightest 5% from', round(float(limit), 3), 'pixels', int(hot.sum()))
