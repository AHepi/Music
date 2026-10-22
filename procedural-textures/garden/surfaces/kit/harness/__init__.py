"""The test rig: cameras, lighting rigs, the test set, jobs, the runner (Blender side), the remote runner, the measuring scripts, self-tests, sheets."""
import os
import sys

HARNESS_ROOT = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HARNESS_ROOT, '..'))
sys.dont_write_bytecode = True
