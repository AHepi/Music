# Measures the rule 10 weight of the left half of any picture, and the notice's bottom-versus-top warmth in a region.
import sys, numpy as np, cv2
for path in sys.argv[1:]:
    picture = cv2.imread(path)
    picture = cv2.resize(picture, (1080, 1920), interpolation=cv2.INTER_AREA)
    grey = cv2.cvtColor(picture, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    edges = cv2.GaussianBlur(np.abs(cv2.Laplacian(cv2.GaussianBlur(grey, (0, 0), 2), cv2.CV_32F)), (0, 0), 25)
    contrast = np.abs(grey - grey.mean())
    weight = edges / edges.mean() + contrast / contrast.mean()
    left_edges = edges[:, :540].sum() / edges.sum(); left_contrast = contrast[:, :540].sum() / contrast.sum()
    print(path.split('/')[-1], f'left half weight {weight[:, :540].sum() / weight.sum():.3f} (detail {left_edges:.3f}, contrast {left_contrast:.3f})')
