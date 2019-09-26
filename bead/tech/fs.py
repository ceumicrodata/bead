import io
import os
import stat
import contextlib
import shutil
import tempfile


class Path(''.__class__):

    def __new__(cls, path):
        assert os.path.sep == '\\' or '\\' not in path, (
            '\\ in file names prevents being cross-platform', path)
        slash_path = os.path.normpath(path).replace('\\', '/')
        return super(Path, cls).__new__(cls, slash_path)

    def __div__(self, other):
        return self.__class__(os.path.join(self, other))

    __truediv__ = __div__


def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

    assert os.path.isdir(path)


def write_file(path, content):
    if isinstance(content, bytes):
        f = open(path, 'wb')
    else:
        f = io.open(path, 'wt', encoding='utf-8')

    with f:
        f.write(content)


def read_file(path):
    with io.open(path, 'rt', encoding='utf-8') as f:
        return f.read()


@contextlib.contextmanager
def temp_dir(dir='.'):
    ensure_directory(dir)

    temp_dir = tempfile.mkdtemp(dir=dir)
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def make_readonly(path):
    '''
    WARNING: It does not work for Windows folders.

    Might fail (silently) on other systems as well.
    '''
    mode = os.stat(path)[stat.ST_MODE]
    os.chmod(path, mode & ~stat.S_IWRITE)


def make_writable(path):
    mode = os.stat(path)[stat.ST_MODE]
    os.chmod(path, mode | stat.S_IWRITE)


def all_subpaths(dir, followlinks=False):
    for root, _dirs, files in os.walk(dir, followlinks=followlinks):
        root = Path(root)
        yield root
        for file in files:
            yield root / file


def rmtree(root, *args, **kwargs):
    for path in all_subpaths(root, followlinks=False):
        if not os.path.islink(path):
            make_writable(path)
    shutil.rmtree(root, *args, **kwargs)
