import pytest
from mongoengine import connect
import mongomock.gridfs

import brew_view.file_writers as writers
from bg_utils.mongo.models import RequestFile


def test_get():
    writer = writers.get("gridfs")
    assert hasattr(writer, "write")


def test_get_fail():
    with pytest.raises(TypeError):
        writers.get("INVALID")


class TestGridfsWriter(object):
    @pytest.fixture
    def gridfs(self):
        return writers.get("gridfs")

    @pytest.fixture(scope="session", autouse=True)
    def run_around(self):
        connect("test", host="mongomock://localhost")
        mongomock.gridfs.enable_gridfs_integration()

    @pytest.fixture(autouse=True)
    def remove_all(self):
        RequestFile.objects().delete()
        assert RequestFile.objects.count() == 0

    def test_write_no_filename(self, gridfs):
        with pytest.raises(ValueError):
            gridfs.write("body")

    @pytest.mark.skip
    def test_write(self, gridfs):
        """Skipping this test until mongomock supports gridfs"""
        mongo_id = gridfs.write("BODY", filename="some_name")
        assert mongo_id is not None
        r_file = RequestFile.objects.get(id=mongo_id)
        assert r_file.body == "BODY"
