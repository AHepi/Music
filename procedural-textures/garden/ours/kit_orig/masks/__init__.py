"""The where-pictures (masks): made once per scene from the real geometry (reader.py), read by name through the bus (bus.py)."""
import glob
import sys

sys.dont_write_bytecode = True


def ensure_cv2():
    """OpenCV is not part of Blender's own Python: when Blender cannot import it, the computer's own copy is appended to the search path (Blender's numpy stays in front)."""
    try:
        import cv2  # noqa: F401
        return True
    except ImportError:
        for pattern in ('/usr/local/lib/python3*/dist-packages', '/usr/lib/python3/dist-packages', '/usr/local/lib/python3*/site-packages'):
            for path in glob.glob(pattern):
                if path not in sys.path:
                    sys.path.append(path)
        try:
            import cv2  # noqa: F401
            return True
        except ImportError:
            return False


ensure_cv2()
