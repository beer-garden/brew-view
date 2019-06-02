import logging

from tornado.gen import coroutine

from brew_view import file_writers
from brew_view import file_readers
from bg_utils.mongo.parser import MongoParser
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.models import Events


class FileListAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    @coroutine
    @authenticated(permissions=[Permissions.FILE_CREATE])
    def post(self):
        """
        ---
        summary: Create a new file
        description: |
            Creates a new file based on the default driver. You can specify
            a different driver with a header.
        consumes:
          - multipart/form-data
        parameters:
          - name: file
            in: formData
            type: file
            description: The file to upload.
        responses:
          201:
            description: A new file has been created
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Beta
        """
        file_writer = self._get_file_writer()

        response = {}
        for key in self.request.files:
            self.request.event.name = Events.FILE_CREATED.name
            fileinfo = self.request.files[key][0]
            filename = fileinfo["filename"]
            body = fileinfo["body"]
            file_id = file_writer.write(body, filename=filename)
            response[key] = {
                "id": file_id,
                "storage_type": "gridfs",
                "filename": filename,
            }

        self.set_status(201)
        self.write(response)

    def _get_file_writer(self):
        storage_type = self.request.headers.get("X-BG-Storage-Type", "gridfs")
        return file_writers.get(storage_type)


class FileAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.FILE_READ])
    def get(self, file_id):
        """
        ---
        summary: Retrieve a specific file, or its metadata
        description: |
            If your storage_type is anything other than gridfs, you probably
            only want to use this endpoint to retrieve metadata, however if
            your storage type is gridfs, then you want to retrieve the actual
            file.
        parameters:
          - name: file_id
            in: path
            required: true
            description: The ID of the file
            type: string
          - name: X-BG-file-meta-only
            in: header
            required: false
            description: If true, will only return JSON metadata about file
            type: string
        produces:
          - application/json
          - application/octet-stream
        responses:
          200:
            description: Will return JSON if X-BG-file-meta-only is true,
              otherwise, it will return the actual file.
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Beta
        """
        meta_only = self.get_bool_header("X-BG-file-meta-only", False)
        request_file, body = file_readers.get("gridfs").read(
            file_id, meta_only=meta_only
        )
        if meta_only:
            self.write(
                self.parser.serialize_request_file(request_file, to_string=False)
            )
        else:
            size = 4096
            self.set_header("Content-Type", "application/octet-stream")
            self.set_header(
                "Content-Disposition", "attachment; filename=%s" % request_file.filename
            )
            while True:
                data = body.read(size)
                if not data:
                    break
                self.write(data)
