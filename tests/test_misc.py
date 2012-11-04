import pytest

import sys
import collections
sys.path.append(".")
import dotkeeper
import tempfile
import shutil
import os


def test_docstrings():
    "Validate that all functions ahve docstrings"
    for thing in dir(dotkeeper):
        thething = getattr(dotkeeper, thing)
        if isinstance(thething, collections.Callable):
            assert thething.__doc__ != None, repr(thing) + " is missing a doc string"

def test_path_fixing():
    "Tests the git-path fixing algorithm"
    assert(dotkeeper.fix_path_to_git(os.path.join(os.environ['HOME'], "foo")) == "$HOME/foo")
    assert(dotkeeper.fix_path_to_git("/etc/passwd") == "etc/passwd")

    assert(dotkeeper.fix_git_to_path("etc/passwd") == "/etc/passwd")
    assert(dotkeeper.fix_git_to_path("$HOME/foo") == os.path.join(os.environ['HOME'], "foo"))
