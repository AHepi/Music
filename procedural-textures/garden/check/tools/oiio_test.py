try:
    import OpenImageIO as oiio
    print('OIIO', oiio.__version__)
except Exception as e:
    print('NO OIIO', e)
import numpy
print('numpy', numpy.__version__)
