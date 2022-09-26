from uuid import uuid4

import pytest
import json
from functools import partial
from tornado import gen

from bg_utils.mongo.models import RequestFile


@pytest.fixture(autouse=True)
def drop_files(app):
    RequestFile.drop_collection()


class TestFileAPI(object):
    @pytest.mark.gen_test
    def test_get_meta_only(
        self, http_client, base_url, request_file_dict, mongo_request_file
    ):
        mongo_request_file.save()

        response = yield http_client.fetch(
            base_url + "/api/vbeta/files/" + str(mongo_request_file.id),
            headers={"X-BG-file-meta-only": "true"},
        )
        assert 200 == response.code
        assert request_file_dict == json.loads(response.body.decode("utf-8"))

    @pytest.mark.gen_test
    def test_get_file(self, http_client, base_url, mongo_request_file):
        mongo_request_file.save()
        response = yield http_client.fetch(
            base_url + "/api/vbeta/files/" + str(mongo_request_file.id)
        )
        assert 200 == response.code
        assert "Content-Type" in response.headers
        assert "Content-Disposition" in response.headers
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=%s" % mongo_request_file.filename
        )
        assert response.body == b""

    @pytest.mark.gen_test
    def test_get_404(self, http_client, base_url, system_id):
        response = yield http_client.fetch(
            base_url + "/api/vbeta/files/" + system_id, raise_error=False
        )
        assert 404 == response.code

    @pytest.fixture
    def boundary(self):
        return uuid4().hex

    @staticmethod
    @gen.coroutine
    def multipart_producer(boundary, filename, body, write):
        boundary_bytes = boundary.encode()
        filename_bytes = filename.encode()
        mtype = "application/octet-stream"
        buf = (
            (b"--%s\r\n" % boundary_bytes)
            + (
                b'Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
                % (filename_bytes, filename_bytes)
            )
            + (b"Content-Type: %s\r\n" % mtype.encode())
            + b"\r\n"
        )
        yield write(buf)
        yield write(body)
        yield write(b"\r\n")
        yield write(b"--%s--\r\n" % boundary_bytes)

    @pytest.mark.gen_test
    @pytest.mark.skip
    def test_post(self, http_client, base_url, boundary, request_file_dict):
        """Skipping until mongomock supports gridfs"""
        headers = {"Content-Type": "multipart/form-data; boundary=%s" % boundary}
        producer = partial(
            self.multipart_producer, boundary, request_file_dict["filename"], b"0x01"
        )
        response = yield http_client.fetch(
            base_url + "/api/vbeta/files/",
            method="POST",
            headers=headers,
            body_producer=producer,
        )
        assert 201 == response.code
        json_response = json.loads(response.body.decode("utf-8"))
        assert "id" in json_response
        assert "storage_type" in json_response
        assert "filename" in json_response
        assert "content_type" in json_response
