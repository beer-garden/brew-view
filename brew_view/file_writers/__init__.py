from brew_view.file_writers import gridfs


def get(name):
    """Get a file writer"""
    fname = str(name).lower()
    if fname == "gridfs":
        return gridfs
    else:
        raise TypeError("Invalid writer type: %s" % name)
