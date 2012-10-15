import pytest

import sys
sys.path.append(".")
import dotkeeper
import tempfile
import shutil
import os


def test_docstrings():
    "Validate that all functions ahve docstrings"
    for thing in dir(dotkeeper):
        thething = getattr(dotkeeper, thing)
        if callable(thething):
            assert thething.__doc__ != None, repr(thing) + " is missing a doc string"

def test_path_fixing():
    "Tests the git-path fixing algorithm"
    assert(dotkeeper.fix_path_to_git("/home/achin/foo") == "home/foo")
    assert(dotkeeper.fix_path_to_git("/etc/passwd") == "etc/passwd")
