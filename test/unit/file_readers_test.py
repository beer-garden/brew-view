import pytest
from mongoengine import connect

import brew_view.file_readers as readers
from bg_utils.mongo.models import RequestFile
from brewtils.test.fixtures import request_file_dict


def test_get():
    reader = readers.get("gridfs")
    assert hasattr(reader, "read")


def test_get_fail():
    with pytest.raises(TypeError):
        readers.get("INVALID")


class TestGridfs(object):
    @pytest.fixture
    def gridfs(self):
        return readers.get("gridfs")

    @pytest.fixture(scope="session", autouse=True)
    def run_around(self):
        connect("test", host="mongomock://localhost")

    @pytest.fixture(autouse=True)
    def remove_all(self):
        RequestFile.objects().delete()
        assert RequestFile.objects.count() == 0

    def test_read_meta_only(self, gridfs, request_file_dict):
        to_save = RequestFile(**request_file_dict)
        to_save.save()
        r_file, body = gridfs.read(to_save.id, meta_only=True)
        assert isinstance(r_file, RequestFile)
        assert body is None

    def test_read(self, gridfs, request_file_dict):
        to_save = RequestFile(**request_file_dict)
        to_save.save()
        r_file, body = gridfs.read(to_save.id, meta_only=False)
        assert body == to_save.body
        assert r_file == to_save
