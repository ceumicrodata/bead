from .test import TestCase
from .box import Box
from .tech.fs import write_file, rmtree
from .tech.timestamp import time_from_user
from .workspace import Workspace
from . import spec as bead_spec


class Test_box_with_beads(TestCase):

    # fixtures
    def box(self):
        box = Box('test', self.new_temp_dir())

        def add_bead(name, kind, timestamp):
            ws = Workspace(self.new_temp_dir() / name)
            ws.create(kind)
            box.store(ws, timestamp)

        add_bead('bead1', 'test-bead1', '20160704T000000000000+0200')
        add_bead('bead2', 'test-bead2', '20160704T162800000000+0200')
        add_bead('BEAD3', 'test-bead3', '20160704T162800000001+0200')
        return box

    def timestamp(self):
        return time_from_user('20160704T162800000000+0200')

    # tests
    def test_all_beads(self, box):
        self.assertEquals(
            set(['bead1', 'bead2', 'BEAD3']),
            set(b.name for b in box.all_beads()))

    def test_find_names(self, box, timestamp):
        (
            exact_match, best_guess, best_guess_timestamp, names
        ) = box.find_names(kind='test-bead1', content_id='', timestamp=timestamp)

        self.assertIsNone(exact_match)
        self.assertEquals('bead1', best_guess)
        self.assertIsNotNone(best_guess_timestamp)
        self.assertEquals(set(['bead1']), set(names))

    def test_find_names_works_even_with_removed_box_directory(self, box, timestamp):
        rmtree(box.directory)
        (
            exact_match, best_guess, best_guess_timestamp, names
        ) = box.find_names(kind='test-bead1', content_id='', timestamp=timestamp)
        self.assertIsNone(exact_match)
        self.assertIsNone(best_guess)
        self.assertIsNone(best_guess_timestamp)
        self.assertSequenceEqual((), names)

    def test_find_with_uppercase_name(self, box, timestamp):
        matches = box.get_context(bead_spec.BEAD_NAME_GLOB, 'BEAD3', timestamp)
        self.assertEquals('BEAD3', matches.best.name)


class Test_box_methods_tolerate_junk_in_box(Test_box_with_beads):

    # fixtures
    def box(self):
        box = Test_box_with_beads.box(self)
        # add junk
        write_file(box.directory / 'some-non-bead-file', 'random bits')
        return box
