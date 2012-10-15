import pytest

import sys
sys.path.append(".")
import dotkeeper
import tempfile
import shutil
import os


class TestMkTree(object):
    def setup_class(cls):
        cls._git_dir = tempfile.mkdtemp(prefix="dktest")
        dotkeeper.git_helper(["init"], git_dir=cls._git_dir)
    
    def teardown_class(cls):
        assert os.path.exists(cls._git_dir)
        shutil.rmtree(cls._git_dir)
        assert not os.path.exists(cls._git_dir)

    def test_mk_tree(self):
        data = "some data"
        hash = dotkeeper.hash_object(contents=data,
                git_dir=self._git_dir)

        assert hash == "7c0646bfd53c1f0ed45ffd81563f30017717ca58"
