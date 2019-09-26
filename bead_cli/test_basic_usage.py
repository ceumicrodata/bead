import os
from bead.test import TestCase
from testtools.content import text_content

from .test_robot import Robot


class Test_basic_command_line(TestCase):

    # fixtures
    def robot(self):
        return self.useFixture(Robot())

    def cli(self, robot):
        return robot.cli

    def cd(self, robot):
        return robot.cd

    def ls(self, robot):
        return robot.ls

    def box_dir(self):
        return self.new_temp_dir()

    # tests
    def test(self, robot, cli, cd, ls, box_dir):
        self.addDetail('home', text_content(robot.home))

        cli('new', 'something')
        self.assertIn('something', robot.stdout)

        cd('something')
        cli('status')
        self.assertNotIn('Inputs', robot.stdout)

        cli('box', 'add', 'default', box_dir)
        cli('save')

        cd('..')
        cli('develop', 'something', 'something-develop')
        self.assertIn(robot.cwd / 'something-develop', ls())

        cd('something-develop')
        cli('input', 'add', 'older-self', 'something')
        cli('status')
        self.assertIn('Inputs', robot.stdout)
        self.assertIn('older-self', robot.stdout)

        cli('web')

        # this might leave behind the empty directory on windows
        cli('nuke')
        cd('..')
        cli('nuke', 'something')

        something_develop_dir = robot.home / 'something-develop'
        if os.path.exists(something_develop_dir):
            # on windows it is not possible to remove
            # the current working directory (nuke does this)
            self.assertNotEqual(os.name, 'posix', 'Must be removed on posix')
            self.assertEqual([], ls(something_develop_dir))
            os.rmdir(something_develop_dir)
        self.assertEqual([], ls(robot.home))
