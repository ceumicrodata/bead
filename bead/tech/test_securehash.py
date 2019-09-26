import os

from ..test import TestCase
from .. import tech

securehash = tech.securehash
write_file = tech.fs.write_file


class Test(TestCase):

    def test_file(self):
        self.given_a_file()
        self.when_file_is_hashed()
        self.then_result_is_an_ascii_string_of_more_than_32_chars()

    def test_bytes(self):
        self.given_some_bytes()
        self.when_bytes_are_hashed()
        self.then_result_is_an_ascii_string_of_more_than_32_chars()

    def test_bytes_and_file_is_compatible(self):
        self.given_some_bytes_and_file_with_those_bytes()
        self.when_file_and_bytes_are_hashed()
        self.then_the_hashes_are_the_same()

    # implementation

    __file = None
    __hashresult = None
    __some_bytes = None

    def given_a_file(self):
        self.__file = self.new_temp_dir() / 'file'
        write_file(self.__file, b'with some content')

    def given_some_bytes(self):
        self.__some_bytes = b'some bytes'

    def given_some_bytes_and_file_with_those_bytes(self):
        self.__some_bytes = b'some bytes'
        self.__file = self.new_temp_dir() / 'file'
        write_file(self.__file, self.__some_bytes)

    def when_bytes_are_hashed(self):
        self.__hashresult = securehash.bytes(self.__some_bytes)

    def when_file_is_hashed(self):
        with open(self.__file, 'rb') as f:
            self.__hashresult = (
                securehash.file(f, os.path.getsize(self.__file))
            )

    def when_file_and_bytes_are_hashed(self):
        with open(self.__file, 'rb') as f:
            self.__hashresult = (
                securehash.bytes(self.__some_bytes),
                securehash.file(f, os.path.getsize(self.__file))
            )

    def then_result_is_an_ascii_string_of_more_than_32_chars(self):
        self.__hashresult.encode('ascii')
        self.assertIsInstance(self.__hashresult, ''.__class__)
        self.assertGreater(len(self.__hashresult), 32)

    def then_the_hashes_are_the_same(self):
        self.assertEquals(*self.__hashresult)
