'''
Proto-Beads & their filesystem layout
'''

import os
import zipfile

from . import layouts
from . import meta
from . import tech
from .bead import Bead

# technology modules
persistence = tech.persistence
securehash = tech.securehash
fs = tech.fs


# generated with `uuidgen -t`
META_VERSION = 'aaa947a6-1f7a-11e6-ba3a-0021cc73492e'


class Workspace(Bead):

    directory = None

    def __init__(self, directory):
        self.directory = fs.Path(os.path.abspath(directory))

    @property
    def is_valid(self):
        dir = self.directory
        return all(
            (
                os.path.isdir(dir / layouts.Workspace.INPUT),
                os.path.isdir(dir / layouts.Workspace.OUTPUT),
                os.path.isdir(dir / layouts.Workspace.TEMP),
                os.path.isfile(dir / layouts.Workspace.BEAD_META)))

    @property
    def meta_path(self):
        return self.directory / layouts.Workspace.BEAD_META

    @property
    def meta(self):
        with open(self.meta_path) as f:
            return persistence.load(f)

    @meta.setter
    def meta(self, meta):
        with open(self.meta_path, 'wt') as f:
            return persistence.dump(meta, f)

    # Bead properties
    @property
    def kind(self):
        return self.meta[meta.KIND]

    @property
    def name(self):
        return os.path.basename(self.directory)

    @property
    def inputs(self):
        return tuple(meta.parse_inputs(self.meta))

    # faked Bead properties
    @property
    def content_id(self):
        # note, that it is not a valid, unique
        # content_id for referencing
        # however it is easily recognisable on graphs
        return f'<WORKSPACE {self.directory}>'

    @property
    def timestamp_str(self):
        return tech.timestamp.timestamp()

    @property
    def box_name(self):
        return '<UNSAVED>'

    # workspace constructors
    def create(self, kind):
        '''
        Set up an empty project structure.

        Works with either an empty directory or a directory to be created.
        '''
        dir = self.directory
        try:
            assert os.listdir(dir) == []
        except OSError:
            pass

        self.create_directories()

        bead_meta = {
            meta.KIND: kind,
            meta.INPUTS: {}}
        fs.write_file(
            dir / layouts.Workspace.BEAD_META,
            persistence.dumps(bead_meta))

        assert self.is_valid

    def create_directories(self):
        dir = self.directory
        fs.ensure_directory(dir)
        fs.ensure_directory(dir / layouts.Workspace.INPUT)
        fs.make_readonly(dir / layouts.Workspace.INPUT)
        fs.ensure_directory(dir / layouts.Workspace.OUTPUT)
        fs.ensure_directory(dir / layouts.Workspace.TEMP)
        fs.ensure_directory(dir / layouts.Workspace.META)

    def pack(self, zipfilename, timestamp, comment):
        '''
        Create archive from workspace.
        '''
        assert not os.path.exists(zipfilename)
        try:
            _ZipCreator().create(zipfilename, self, timestamp, comment)
        except (RuntimeError, Exception):
            if os.path.exists(zipfilename):
                os.remove(zipfilename)
            raise

    def has_input(self, input_nick):
        '''
        Is there an input defined for input_nick?

        NOTE: it is not necessarily loaded!
        '''
        return input_nick in self.meta[meta.INPUTS]

    def is_loaded(self, input_nick):
        return os.path.isdir(
            self.directory / layouts.Workspace.INPUT / input_nick)

    def add_input(self, input_nick, kind, content_id, timestamp_str):
        m = self.meta
        m[meta.INPUTS][input_nick] = {
            meta.INPUT_KIND: kind,
            meta.INPUT_CONTENT_ID: content_id,
            meta.INPUT_FREEZE_TIME: timestamp_str}
        self.meta = m

    def delete_input(self, input_nick):
        assert self.has_input(input_nick)
        if self.is_loaded(input_nick):
            self.unload(input_nick)
        m = self.meta
        del m[meta.INPUTS][input_nick]
        self.meta = m

    def load(self, input_nick, bead):
        '''
        Make output data files in bead available under input directory
        '''
        input_dir = self.directory / layouts.Workspace.INPUT
        fs.make_writable(input_dir)
        try:
            self.add_input(
                input_nick,
                bead.kind, bead.content_id, bead.timestamp_str)
            destination_dir = input_dir / input_nick
            bead.unpack_data_to(destination_dir)
            for f in fs.all_subpaths(destination_dir):
                fs.make_readonly(f)
        finally:
            fs.make_readonly(input_dir)

    def unload(self, input_nick):
        '''
        Remove files for given input
        '''
        assert self.has_input(input_nick)
        input_dir = self.directory / layouts.Workspace.INPUT
        fs.make_writable(input_dir)
        try:
            fs.rmtree(input_dir / input_nick)
        finally:
            fs.make_readonly(input_dir)

    def __repr__(self):
        # default values are printed as repr of the value
        return self.directory

    @classmethod
    def for_current_working_directory(cls):
        '''
        Create Workspace based on current working directory.

        Determine the correct Workspace for the current working directory.
        As a result, the returned workspace may be for a parent directory,
        if the cwd is under a valid workspace, but not at its root.

        Can return an invalid Workspace.
        '''
        cwd = cls(os.getcwd())
        ws = cwd
        while not ws.is_valid:
            parent = ws.directory / '..'
            if parent == ws.directory:
                return cwd
            ws = cls(parent)
        return ws


class _ZipCreator(object):
    def __init__(self):
        self.hashes = {}
        self.zipfile = None

    def add_hash(self, path, hash):
        assert path not in self.hashes
        self.hashes[path] = hash

    def add_file(self, path, zip_path):
        self.zipfile.write(path, zip_path)
        self.add_hash(
            zip_path,
            securehash.file(open(path, 'rb'), os.path.getsize(path)))

    def add_path(self, path, zip_path):
        if os.path.isdir(path):
            self.add_directory(path, zip_path)
        else:
            assert os.path.isfile(path), '%s is neither a file nor a directory' % path
            self.add_file(path, zip_path)

    def add_directory(self, path, zip_path):
        for f in os.listdir(path):
            self.add_path(path / f, zip_path / f)

    def add_string_content(self, zip_path, string):
        bytes = string.encode('utf-8')
        self.zipfile.writestr(zip_path, bytes)
        self.add_hash(zip_path, securehash.bytes(bytes))

    def create(self, zip_file_name, workspace, timestamp, comment):
        assert workspace.is_valid
        try:
            with zipfile.ZipFile(
                zip_file_name,
                mode='w',
                compression=zipfile.ZIP_DEFLATED,
                allowZip64=True,
            ) as self.zipfile:
                self.zipfile.comment = comment.encode('utf-8')
                self.add_data(workspace)
                self.add_code(workspace)
                self.add_meta(workspace, timestamp)
        finally:
            self.zipfile = None

    def add_code(self, workspace):
        source_directory = workspace.directory

        def is_code(f):
            return f not in {
                layouts.Workspace.INPUT,
                layouts.Workspace.OUTPUT,
                layouts.Workspace.META,
                layouts.Workspace.TEMP}

        for f in sorted(os.listdir(source_directory)):
            if is_code(f):
                self.add_path(
                    source_directory / f,
                    layouts.Archive.CODE / f)

    def add_data(self, workspace):
        self.add_directory(
            workspace.directory / layouts.Workspace.OUTPUT,
            layouts.Archive.DATA)

    def add_meta(self, workspace, timestamp):
        bead_meta = {
            meta.META_VERSION: META_VERSION,
            meta.KIND: workspace.kind,
            meta.FREEZE_TIME: timestamp,
            meta.INPUTS: {
                input.name: {
                    meta.INPUT_KIND: input.kind,
                    meta.INPUT_CONTENT_ID: input.content_id,
                    meta.INPUT_FREEZE_TIME: input.timestamp_str}
                for input in workspace.inputs},
            meta.FREEZE_NAME: workspace.name}

        self.add_string_content(
            layouts.Archive.BEAD_META,
            persistence.dumps(bead_meta))
        self.add_string_content(
            layouts.Archive.MANIFEST,
            persistence.dumps(self.hashes))
