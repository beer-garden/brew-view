from brew_view.file_readers import gridfs


def get(name):
    """Get a file_reader"""
    fname = str(name).lower()
    if fname == "gridfs":
        return gridfs
    else:
        raise TypeError("Invalid reader type: %s" % name)
