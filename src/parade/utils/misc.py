"""Helper functions which don't fit anywhere else"""
import os

from shutil import copy2, copystat


def copytree(src, dst, ignore=None):
    """
    Since the original function always creates the directory, to resolve
    the issue a new function had to be created. It's a simple copy and
    was reduced for this case.

    More info at:
    https://github.com/scrapy/scrapy/pull/2005
    """
    names = os.listdir(src)
    ignored_names = ignore(src, names)

    if not os.path.exists(dst):
        os.makedirs(dst)

    for name in names:
        if name in ignored_names:
            continue

        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if os.path.isdir(srcname):
            copytree(srcname, dstname, ignore)
        else:
            copy2(srcname, dstname)
    copystat(src, dst)


def merge_dict(source, destination):
    """
    run me with nosetests --with-doctest file.py

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '0' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '4' } } }
    >>> merge_dict(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '4' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge_dict(value, node)
        else:
            destination[key] = value
    return destination
