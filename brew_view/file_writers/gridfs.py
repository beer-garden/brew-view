from bg_utils.mongo.models import RequestFile


def write(body, **kwargs):
    """Write the given body to gridfs.

    Args:
        body: Bytes

    Keyword Args:
        filename: required, name of the file.
        encoding: default is None

    Returns:
        The ID of the RequestFile that was written to the database.

    """
    filename = kwargs.get("filename")
    if not filename:
        raise ValueError("Cannot write a gridfs document without a filename.")

    encoding = kwargs.get("encoding")
    r_file = RequestFile(filename=filename)
    r_file.body.new_file(encoding=encoding)
    r_file.body.write(body)
    r_file.body.close()
    r_file.save()
    return str(r_file.id)
