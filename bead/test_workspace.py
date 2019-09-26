from .test import TestCase, chdir
from . import workspace as m

import os
import zipfile

from .archive import Archive
from . import layouts
from . import tech

write_file = tech.fs.write_file
ensure_directory = tech.fs.ensure_directory
temp_dir = tech.fs.temp_dir
timestamp = tech.timestamp.timestamp
Path = tech.fs.Path

A_KIND = 'an arbitrary identifier that is not used by chance'


class Test_create(TestCase):

    def test_valid(self):
        self.given_an_empty_directory()
        self.when_initialized()
        self.then_directory_is_a_valid_bead_dir()

    def test_has_no_inputs(self):
        self.given_an_empty_directory()
        self.when_initialized()
        self.then_workspace_has_no_inputs()

    def test_of_specified_kind(self):
        self.given_an_empty_directory()
        self.when_initialized()
        self.then_workspace_is_of_specified_kind()

    # implementation

    __workspace_dir = None

    @property
    def workspace(self):
        return m.Workspace(self.__workspace_dir)

    def given_an_empty_directory(self):
        self.__workspace_dir = self.new_temp_dir()

    def when_initialized(self):
        self.workspace.create(A_KIND)

    def then_directory_is_a_valid_bead_dir(self):
        self.assertTrue(self.workspace.is_valid)

    def then_workspace_has_no_inputs(self):
        self.assertFalse(self.workspace.has_input('bead1'))
        self.assertFalse(self.workspace.is_loaded('bead1'))
        self.assertFalse(self.workspace.inputs)

    def then_workspace_is_of_specified_kind(self):
        self.assertEquals(A_KIND, self.workspace.kind)


class Test_for_current_working_directory(TestCase):

    def test_non_workspace(self):
        root = self.new_temp_dir()
        with chdir(root):
            ws = m.Workspace.for_current_working_directory()
        self.assertEquals(tech.fs.Path(root), ws.directory)

    def test_workspace_root(self):
        root = self.new_temp_dir()
        workspace = m.Workspace(root)
        workspace.create(A_KIND)
        with chdir(root):
            ws = m.Workspace.for_current_working_directory()
        self.assertEquals(tech.fs.Path(root), ws.directory)

    def test_workspace_above_root(self):
        root = self.new_temp_dir()
        workspace = m.Workspace(root)
        workspace.create(A_KIND)
        with chdir(root / layouts.Workspace.INPUT):
            ws = m.Workspace.for_current_working_directory()
        self.assertEquals(tech.fs.Path(root), ws.directory)


class Test_pack(TestCase):

    def test_creates_valid_archive(self):
        self.given_a_workspace()
        self.when_archived()
        self.then_archive_is_valid_bead()

    def test_archives_all_content(self):
        self.given_a_workspace()
        self.when_archived()
        self.then_archive_contains_files_from_bead_directory()

    def test_not_saved_content(self):
        self.given_a_workspace()
        self.when_archived()
        self.then_archive_does_not_contain_workspace_meta_and_temp_files()

    def test_archive_has_comment(self):
        self.given_a_workspace()
        self.when_archived()
        self.then_archive_has_comment()

    # implementation

    __workspace_dir = None
    __zipdir = None
    __zipfile = None
    __SOURCE1 = b's1'
    __SOURCE2 = b's2'
    __OUTPUT1 = b'o1'
    assert __SOURCE2 != __SOURCE1
    __BEAD_COMMENT = 'custom bead comment'

    @property
    def workspace(self):
        return m.Workspace(self.__workspace_dir)

    def given_a_workspace(self):
        self.__workspace_dir = self.new_temp_dir()
        self.workspace.create(A_KIND)
        layout = layouts.Workspace

        write_file(
            self.__workspace_dir / layout.TEMP / 'README',
            'temporary directory')
        write_file(
            self.__workspace_dir / layout.OUTPUT / 'output1',
            self.__OUTPUT1)
        write_file(self.__workspace_dir / 'source1', self.__SOURCE1)
        ensure_directory(self.__workspace_dir / 'subdir')
        write_file(self.__workspace_dir / 'subdir/source2', self.__SOURCE2)

    def when_archived(self):
        self.__zipdir = self.new_temp_dir()
        self.__zipfile = self.__zipdir / 'bead.zip'
        self.workspace.pack(self.__zipfile, timestamp(), self.__BEAD_COMMENT)

    def then_archive_contains_files_from_bead_directory(self):
        with zipfile.ZipFile(self.__zipfile) as z:
            layout = layouts.Archive

            self.assertEquals(self.__OUTPUT1, z.read(layout.DATA / 'output1'))
            self.assertEquals(self.__SOURCE1, z.read(layout.CODE / 'source1'))
            self.assertEquals(self.__SOURCE2, z.read(layout.CODE / 'subdir/source2'))

            files = z.namelist()
            self.assertIn(layout.BEAD_META, files)
            self.assertIn(layout.MANIFEST, files)

    def then_archive_is_valid_bead(self):
        bead = Archive(self.__zipfile)
        self.assertTrue(bead.is_valid)

    def then_archive_has_comment(self):
        with zipfile.ZipFile(self.__zipfile) as z:
            self.assertEquals(self.__BEAD_COMMENT, z.comment.decode('utf-8'))

    def then_archive_does_not_contain_workspace_meta_and_temp_files(self):
        def does_not_contain(workspace_path):
            with zipfile.ZipFile(self.__zipfile) as z:
                archive_path = layouts.Archive.CODE / workspace_path
                self.assertRaises(KeyError, z.getinfo, archive_path)

        does_not_contain(layouts.Workspace.BEAD_META)
        does_not_contain(layouts.Workspace.TEMP / 'README')


class Test_pack_stability(TestCase):

    def test_directory_name_data_and_timestamp_determines_content_ids(self):
        TS = '20150910T093724802366+0200'

        # note: it is important to create the same bead in
        # two different directories
        def make_bead():
            output = self.new_temp_dir() / 'bead.zip'
            ws = m.Workspace(self.new_temp_dir() / 'a bead')
            ws.create(A_KIND)
            write_file(ws.directory / 'source1', 'code to produce output')
            write_file(ws.directory / 'output/output1', TS)
            ws.pack(output, TS, comment='')
            return Archive(output)

        bead1 = make_bead()
        bead2 = make_bead()
        self.assertEquals(bead1.content_id, bead2.content_id)


def make_bead(path, filespecs):
    with temp_dir() as root:
        workspace = m.Workspace(root)
        workspace.create(A_KIND)
        for filename, content in filespecs.items():
            write_file(workspace.directory / filename, content)
        workspace.pack(path, timestamp(), 'no comment')


class Test_load(TestCase):

    def test_makes_bead_files_available_under_input(self):
        self.given_a_workspace()
        self.when_loading_a_bead()
        self.then_data_files_in_bead_are_available_in_workspace()

    def test_loaded_inputs_are_read_only(self):
        self.given_a_workspace()
        self.when_loading_a_bead()
        self.then_extracted_files_under_input_are_readonly()

    def test_load_adds_input_to_bead_meta(self):
        self.given_a_workspace()
        self.when_loading_a_bead()
        self.then_input_info_is_added_to_bead_meta()

    def test_loading_more_than_one_bead(self):
        self.given_a_workspace()
        self.when_loading_a_bead()
        self.then_another_bead_can_be_loaded()

    # implementation

    __workspace_dir = None

    @property
    def workspace(self):
        return m.Workspace(self.__workspace_dir)

    def given_a_workspace(self):
        self.__workspace_dir = self.new_temp_dir()
        self.workspace.create(A_KIND)

    def _load_a_bead(self, input_nick):
        path_of_bead_to_load = self.new_temp_dir() / 'bead.zip'
        make_bead(
            path_of_bead_to_load,
            {
                'output/output1':
                f'data for {input_nick}'.encode('utf-8')
            }
        )
        self.workspace.load(input_nick, Archive(path_of_bead_to_load))

    def when_loading_a_bead(self):
        self._load_a_bead('bead1')

    def then_data_files_in_bead_are_available_in_workspace(self):
        with open(self.__workspace_dir / 'input/bead1/output1', 'rb') as f:
            self.assertEquals(b'data for bead1', f.read())

    def then_extracted_files_under_input_are_readonly(self):
        root = self.__workspace_dir / 'input/bead1'
        self.assertTrue(os.path.exists(root))
        self.assertRaises(IOError, open, root / 'output1', 'ab')
        # also folders are read only - this does not work on Windows
        if os.name == 'posix':
            self.assertRaises(IOError, open, root / 'new-file', 'wb')

    def then_input_info_is_added_to_bead_meta(self):
        self.assertTrue(self.workspace.has_input('bead1'))
        self.assertTrue(self.workspace.is_loaded('bead1'))

    def then_another_bead_can_be_loaded(self):
        self._load_a_bead('bead2')


def unzip(archive_path, directory):
    ensure_directory(directory)
    with zipfile.ZipFile(archive_path) as z:
        z.extractall(directory)


def zip_up(directory, archive_path):
    with zipfile.ZipFile(archive_path, 'w') as z:
        def add(path, zip_path):
            if os.path.isdir(path):
                for name in os.listdir(path):
                    add(path / name, zip_path / name)
            else:
                z.write(path, zip_path)
        add(directory, Path('/'))


class Test_is_valid(TestCase):

    # fixtures

    def workspace(self):
        workspace = m.Workspace(self.new_temp_dir())
        workspace.create(A_KIND)
        return workspace

    def timestamp(self):
        return '20150930T093724802366+0200'

    def archive_path(self, workspace, timestamp):
        archive_path = self.new_temp_dir() / 'bead.zip'
        workspace.pack(archive_path, timestamp, comment=archive_path)
        return archive_path

    def archive_with_two_files_path(self, workspace, timestamp):
        write_file(workspace.directory / 'code1', 'code1')
        write_file(workspace.directory / 'output/data1', 'data1')
        return self.archive_path(workspace, timestamp)

    def unzipped_archive_path(self, archive_with_two_files_path):
        path = self.new_temp_dir()
        unzip(archive_with_two_files_path, path)
        return path

    def archive(self, archive_path):
        return Archive(archive_path)

    # tests

    def test_newly_created_bead_is_valid(self, archive_with_two_files_path):
        self.assertTrue(Archive(archive_with_two_files_path).is_valid)

    def test_adding_a_data_file_to_an_archive_makes_bead_invalid(self, archive_path):
        with zipfile.ZipFile(archive_path, 'a') as z:
            z.writestr(layouts.Archive.DATA / 'extra_file', b'something')

        self.assertFalse(Archive(archive_path).is_valid)

    def test_adding_a_code_file_to_an_archive_makes_bead_invalid(self, archive_path):
        with zipfile.ZipFile(archive_path, 'a') as z:
            z.writestr(layouts.Archive.CODE / 'extra_file', b'something')

        self.assertFalse(Archive(archive_path).is_valid)

    def test_unzipping_and_zipping_an_archive_remains_valid(self, unzipped_archive_path):
        rezipped_archive_path = self.new_temp_dir() / 'rezipped_archive.zip'
        zip_up(unzipped_archive_path, rezipped_archive_path)

        self.assertTrue(Archive(rezipped_archive_path).is_valid)

    def test_deleting_a_file_in_the_manifest_makes_the_bead_invalid(self, unzipped_archive_path):
        os.remove(unzipped_archive_path / layouts.Archive.CODE / 'code1')
        modified_archive_path = self.new_temp_dir() / 'modified_archive.zip'
        zip_up(unzipped_archive_path, modified_archive_path)

        self.assertFalse(Archive(modified_archive_path).is_valid)

    def test_changing_a_file_makes_the_bead_invalid(self, unzipped_archive_path):
        write_file(unzipped_archive_path / layouts.Archive.CODE / 'code1', b'HACKED')
        modified_archive_path = self.new_temp_dir() / 'modified_archive.zip'
        zip_up(unzipped_archive_path, modified_archive_path)

        self.assertFalse(Archive(modified_archive_path).is_valid)
