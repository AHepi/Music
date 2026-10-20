# verifier: runs the builder's geometry_route.py as it is, with byte-code writing switched off (nothing written outside verify/)
import os, runpy, sys
sys.dont_write_bytecode = True
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'generator', 'geometry_route.py'), run_name='__main__')
