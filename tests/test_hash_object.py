import pytest

import sys
sys.path.append(".")
import dotkeeper
import tempfile
import shutil
import os


class TestHashObject(object):

    def setup_class(cls):
        cls._git_dir = tempfile.mkdtemp(prefix="dktest")
        dotkeeper.git_helper(["init"], git_dir=cls._git_dir)
    
    def teardown_class(cls):
        assert os.path.exists(cls._git_dir)
        shutil.rmtree(cls._git_dir)
        assert not os.path.exists(cls._git_dir)

    def test_hash_from_file(self, tmpdir):
        assert tmpdir.check()
        f = tmpdir.join("test")
        data = "some data"
        f.write(data)

        hash = dotkeeper.hash_object(filename=str(f), git_dir = self._git_dir)

        assert hash == "7c0646bfd53c1f0ed45ffd81563f30017717ca58"

    def test_hash_fron_contents(self):
        data = "some data"
        hash = dotkeeper.hash_object(contents=data, git_dir = self._git_dir)
        assert hash == "7c0646bfd53c1f0ed45ffd81563f30017717ca58"

        got_data = dotkeeper.cat_file(hash, git_dir = self._git_dir)
        assert got_data == data
    
    def test_hash_from_multiline_contents(self):
        data = "some data\nand some more data"
        hash = dotkeeper.hash_object(contents=data, git_dir = self._git_dir)
        assert hash == "65927aaf6dc83c89b5980b7da5344f9bd968fc28"

        got_data = dotkeeper.cat_file(hash, git_dir = self._git_dir)
        assert got_data == data

    def test_hash_exception(self):
        with pytest.raises(dotkeeper.GitException):
            dotkeeper.hash_object()

