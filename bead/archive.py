from copy import deepcopy
import functools
import io
import os
import re
import shutil
import zipfile

from .bead import UnpackableBead
from . import tech
from . import layouts
from . import meta

# technology modules
timestamp = tech.timestamp
securehash = tech.securehash
persistence = tech.persistence


def bead_name_from_file_path(path):
    '''
    Parse bead name from a file path.

    Might return a simpler name than intended
    '''
    name_with_timestamp, ext = os.path.splitext(os.path.basename(path))
    # assert ext == '.zip'  # not enforced to allow having beads with different extensions
    name = re.sub('_[0-9]{8}(?:[tT][-+0-9]*)?$', '', name_with_timestamp)
    return name


assert 'bead-2015v3' == bead_name_from_file_path('bead-2015v3.zip')
assert 'bead-2015v3' == bead_name_from_file_path('bead-2015v3_20150923.zip')
assert 'bead-2015v3' == bead_name_from_file_path('bead-2015v3_20150923T010203012345+0200.zip')
assert 'bead-2015v3' == bead_name_from_file_path('bead-2015v3_20150923T010203012345-0200.zip')


class InvalidArchive(Exception):
    """Not a valid bead archive"""


class Archive(UnpackableBead):

    def __init__(self, filename, box_name=''):
        self.archive_filename = filename
        self.box_name = box_name
        self.name = bead_name_from_file_path(filename)
        self.zipfile = None
        self._meta = self._load_meta()
        self._content_id = None

    def __zipfile_user(method):
        # method is called with the zipfile opened
        @functools.wraps(method)
        def f(self, *args, **kwargs):
            if self.zipfile:
                return method(self, *args, **kwargs)
            try:
                with zipfile.ZipFile(self.archive_filename) as self.zipfile:
                    return method(self, *args, **kwargs)
            except (zipfile.BadZipFile, OSError, IOError):
                raise InvalidArchive(self.archive_filename)
            finally:
                self.zipfile = None
        return f

    # -
    # FIXME: Archive.is_valid is too costly for a property
    # in fact it is so costly in some cases, that it the user is worth
    # notifying that it is happening, see verify_with_feedback(archive)
    @property
    @__zipfile_user
    def is_valid(self):
        '''
        verify, that
        - all files under code, data, meta are present in the manifest
          file and they match their content_id (extra files are allowed
          in the archive, but not as data or code files)
        - the BEAD_META file is valid
            - has meta version
            - has kind
            - has freeze time
            - has freezed name
            - has inputs (even if empty)
        '''
        return all(self._checks())

    def _checks(self):
        yield self._has_well_formed_meta()
        yield self._bead_creation_time_is_in_the_past()
        yield self._extra_file() is None
        yield self._file_with_different_content_id() is None

    def _has_well_formed_meta(self):
        m = self.meta
        keys = (
            meta.META_VERSION,
            meta.KIND,
            meta.FREEZE_TIME,
            meta.FREEZE_NAME,
            meta.INPUTS)
        return all(key in m for key in keys)

    def _bead_creation_time_is_in_the_past(self):
        read_time = timestamp.time_from_timestamp
        now = read_time(timestamp.timestamp())
        freeze_time = read_time(self.meta[meta.FREEZE_TIME])
        # we could be strict, but unfortunately on windows the resolution
        # of datetime.now is low yielding the same value for multiple calls
        # so we need that = in the <= to get the tests pass
        # see e.g. https://blogs.msdn.microsoft.com/ericlippert/
        #                 2010/04/08/precision-and-accuracy-of-datetime/
        return freeze_time <= now

    @__zipfile_user
    def _extra_file(self):
        data_dir_prefix = layouts.Archive.DATA + '/'
        code_dir_prefix = layouts.Archive.CODE + '/'
        manifest = self.manifest
        # check that there are no extra files
        for name in self.zipfile.namelist():
            is_data = name.startswith(data_dir_prefix)
            is_code = name.startswith(code_dir_prefix)
            if is_data or is_code:
                if name not in manifest:
                    # unexpected extra file!
                    return name

    @__zipfile_user
    def _file_with_different_content_id(self):
        for name, hash in self.manifest.items():
            try:
                info = self.zipfile.getinfo(name)
            except KeyError:
                return name
            archived_hash = securehash.file(self.zipfile.open(info), info.file_size)
            if hash != archived_hash:
                return name

    @property
    @__zipfile_user
    def manifest(self):
        with self.zipfile.open(layouts.Archive.MANIFEST) as f:
            return persistence.load(io.TextIOWrapper(f, encoding='utf-8'))

    @property
    def content_id(self):
        if self._content_id is None:
            self._content_id = self.calculate_content_id()
        return self._content_id

    @__zipfile_user
    def calculate_content_id(self):
        # there is currently only one meta version
        # and it must match the one defined in the workspace module
        assert self._meta[meta.META_VERSION] == 'aaa947a6-1f7a-11e6-ba3a-0021cc73492e'
        zipinfo = self.zipfile.getinfo(layouts.Archive.MANIFEST)
        with self.zipfile.open(zipinfo) as f:
            return securehash.file(f, zipinfo.file_size)

    @property
    def kind(self):
        return self._meta[meta.KIND]

    @property
    def timestamp_str(self):
        return self._meta[meta.FREEZE_TIME]

    @property
    def meta(self):
        # create a copy, so that returned meta can be modified without causing
        # harm to this Archive instance
        return deepcopy(self._meta)

    @property
    def inputs(self):
        return tuple(meta.parse_inputs(self.meta))

    # -
    @__zipfile_user
    def _load_meta(self):
        try:
            with self.zipfile.open(layouts.Archive.BEAD_META) as f:
                try:
                    return persistence.load(io.TextIOWrapper(f, encoding='utf-8'))
                except persistence.ReadError:
                    raise InvalidArchive(self.archive_filename)
        except:
            raise InvalidArchive(self.archive_filename)

    @__zipfile_user
    def extract_file(self, zip_path, fs_path):
        '''
            Extract zip_path from zipfile to fs_path.
        '''
        fs_path = os.path.normpath(fs_path)

        upperdirs = os.path.dirname(fs_path)
        if upperdirs:
            tech.fs.ensure_directory(upperdirs)

        with self.zipfile.open(zip_path) as source:
            with open(fs_path, 'wb') as target:
                shutil.copyfileobj(source, target)

    @__zipfile_user
    def extract_dir(self, zip_dir, fs_dir):
        '''
            Extract all files from zipfile under zip_dir to fs_dir.
        '''

        tech.fs.ensure_directory(fs_dir)

        zip_dir_prefix = zip_dir + '/'
        zip_dir_prefix_len = len(zip_dir_prefix)

        for zip_path in self.zipfile.namelist():
            if not zip_path.startswith(zip_dir_prefix):
                continue
            fs_path = fs_dir / zip_path[zip_dir_prefix_len:]
            self.extract_file(zip_path, fs_path)

    def unpack_code_to(self, fs_dir):
        self.extract_dir(layouts.Archive.CODE, fs_dir)

    def unpack_data_to(self, fs_dir):
        self.extract_dir(layouts.Archive.DATA, fs_dir)

    def unpack_meta_to(self, workspace):
        workspace.meta = self.meta
