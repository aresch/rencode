from rencode._rencode import Ext, __version__, dumps, loads


def dump(data, fp, **kwargs):
    """
    Serialize data as rencode v2 and write to a file-like object.
    """
    fp.write(dumps(data, **kwargs))


def load(fp, **kwargs):
    """
    Read from a file-like object and deserialize rencode v2 data.
    """
    return loads(fp.read(), **kwargs)


__all__ = ["Ext", "__version__", "dump", "dumps", "load", "loads"]
