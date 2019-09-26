from .test import TestCase
from . import archive as m

import os
import zipfile

from . import layouts


class Test_Archive(TestCase):

    def test_extract_file(self):
        self.given_a_bead()
        self.when_file1_is_extracted()
        self.then_file1_has_the_expected_content()

    def test_extract_dir(self):
        self.given_a_bead()
        self.when_a_directory_is_extracted()
        self.then_directory_has_the_expected_files()
        self.then_file1_has_the_expected_content()

    def test_extract_nonexistant_dir(self):
        self.given_a_bead()
        self.when_a_nonexistent_directory_is_extracted()
        self.then_an_empty_directory_is_created()

    def test_content_id(self):
        self.given_a_bead()
        self.when_content_id_is_checked()
        self.then_content_id_is_a_string()

    # implementation

    __bead = None
    __extractedfile = None
    __extracteddir = None
    __content_id = None

    def given_a_bead(self):
        # FIXME: test_archive.given_a_bead is fragile and yields an invalid BEAD
        self.__bead = self.new_temp_dir() / 'bead.zip'
        with zipfile.ZipFile(self.__bead, 'w') as z:
            z.writestr(
                layouts.Archive.BEAD_META,
                b'{"meta_version": "aaa947a6-1f7a-11e6-ba3a-0021cc73492e"}')
            z.writestr('somefile1', b'''somefile1's known content''')
            z.writestr('path/file1', b'''?? file1's known content''')
            z.writestr('path/to/file1', b'''file1's known content''')
            z.writestr('path/to/file2', b'''file2's known content''')
            z.writestr(layouts.Archive.MANIFEST, b'some manifest')

    def when_file1_is_extracted(self):
        self.__extractedfile = self.new_temp_dir() / 'extracted_file'
        bead = m.Archive(self.__bead)
        bead.extract_file('path/to/file1', self.__extractedfile)

    def then_file1_has_the_expected_content(self):
        with open(self.__extractedfile, 'rb') as f:
            self.assertEquals(b'''file1's known content''', f.read())

    def when_a_directory_is_extracted(self):
        self.__extracteddir = self.new_temp_dir() / 'destination dir'
        bead = m.Archive(self.__bead)
        bead.extract_dir('path/to', self.__extracteddir)
        self.__extractedfile = os.path.join(self.__extracteddir, 'file1')

    def then_directory_has_the_expected_files(self):
        self.assertEquals(
            {'file1', 'file2'},
            set(os.listdir(self.__extracteddir))
        )

    def when_content_id_is_checked(self):
        bead = m.Archive(self.__bead)
        self.__content_id = bead.content_id

    def then_content_id_is_a_string(self):
        self.assertIsInstance(self.__content_id, ''.__class__)

    def when_a_nonexistent_directory_is_extracted(self):
        self.__extracteddir = self.new_temp_dir() / 'destination dir'
        bead = m.Archive(self.__bead)
        bead.extract_dir('path/to/nonexistent', self.__extracteddir)

    def then_an_empty_directory_is_created(self):
        self.assertTrue(os.path.isdir(self.__extracteddir))
        self.assertEquals([], os.listdir(self.__extracteddir))
