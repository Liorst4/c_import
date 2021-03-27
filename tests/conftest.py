import os
import sys

# Make c_import importable from the tests
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..'
)))
