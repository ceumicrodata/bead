from bead.test import TestCase
from testtools.matchers import FileContains, Contains, FileExists

from bead.workspace import Workspace
from bead import layouts
from . import test_fixtures as fixtures


class Test_develop(TestCase, fixtures.RobotAndBeads):

    # tests
    def test_by_name(self, robot, bead_a):
        robot.cli('develop', bead_a)

        self.assertTrue(Workspace(robot.cwd / bead_a).is_valid)
        self.assertThat(robot.cwd / bead_a / 'README', FileContains(bead_a))

    def test_missing_bead(self, robot, bead_a):
        robot.cli('box', 'forget', 'box')
        try:
            robot.cli('develop', bead_a)
        except SystemExit:
            self.assertThat(robot.stderr, Contains('Bead'))
            self.assertThat(robot.stderr, Contains('not found'))
        else:
            self.fail('develop should have exited on missing bead')

    def assert_develop_version(self, robot, timestamp, *bead_spec):
        assert bead_spec[0] == 'bead_with_history'
        robot.cli('develop', *bead_spec)
        self.assertThat(
            robot.cwd / 'bead_with_history' / 'sentinel-' + timestamp,
            FileExists())

    def test_last_version(self, robot, bead_with_history):
        self.assert_develop_version(robot, fixtures.TS_LAST, bead_with_history)

    def test_at_time(self, robot, bead_with_history):
        self.assert_develop_version(robot, fixtures.TS1, 'bead_with_history', '-t', fixtures.TS1)

    def test_hacked_bead_is_detected(self, robot, hacked_bead):
        self.assertRaises(SystemExit, robot.cli, 'develop', hacked_bead)
        self.assertThat(robot.stderr, Contains('ERROR'))

    def test_extract_output(self, robot, bead_a):
        robot.cli('develop', '-x', bead_a)
        ws = robot.cwd / bead_a

        self.assertTrue(Workspace(ws).is_valid)

        # output must be unpacked as well!
        self.assertThat(
            ws / layouts.Workspace.OUTPUT / 'README',
            FileContains(bead_a))
