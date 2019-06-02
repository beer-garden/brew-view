from bg_utils.mongo.models import RequestFile


def read(file_id, **kwargs):
    """Read a file from gridfs."""
    r_file = RequestFile.objects.get(id=file_id)
    if kwargs.get("meta_only", False):
        return r_file, None

    return r_file, r_file.body
