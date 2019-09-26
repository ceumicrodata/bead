# coding: utf-8
from ..test import TestCase
from . import persistence as m


def get_structure():
    return {
        '1': 'árvíztűrő',
        'a': 'tükörfúrógép',
        'z': [1, '', 3.14, {}]
    }


class Test(TestCase):

    def test_streams(self):
        self.given_a_persisted_structure_as_a_file()
        self.when_file_is_read_back()
        self.then_it_equals_the_original_structure()

    def test_strings(self):
        self.given_a_persisted_structure_as_a_string()
        self.when_string_is_parsed_back()
        self.then_it_equals_the_original_structure()

    # implementation

    __file = None
    __string = None
    __structure = None

    def given_a_persisted_structure_as_a_file(self):
        self.__file = self.new_temp_dir() / 'file'
        with open(self.__file, 'w') as f:
            m.dump(get_structure(), f)

    def given_a_persisted_structure_as_a_string(self):
        self.__string = m.dumps(get_structure())

    def when_file_is_read_back(self):
        with open(self.__file, 'r') as f:
            self.__structure = m.load(f)

    def when_string_is_parsed_back(self):
        self.__structure = m.loads(self.__string)

    def then_it_equals_the_original_structure(self):
        self.assertEquals(get_structure(), self.__structure)
