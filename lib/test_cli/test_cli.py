from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from ..test import TestCase, TempDir
# from ..test import xfail
from testtools.matchers import FileContains, Not, Contains, FileExists

import os
from ..pkg.workspace import Workspace
from .. import tech
from ..translations import add_translation
from .robot import Robot
from .. import repos


# timestamps
TS1 = '20150901_151015_1'
TS2 = '20150901_151016_2'


class PackageFixtures(object):

    # fixtures
    def robot(self):
        '''
        I am a robot user with a repo
        '''
        robot = self.useFixture(Robot())
        repo_dir = robot.cwd / 'repo'
        os.makedirs(repo_dir)
        robot.cli('repo', 'add', 'repo', repo_dir)
        return robot

    def repo(self, robot):
        with robot.environment:
            return repos.get('repo')

    def packages(self):
        return {}

    def _new_package(self, robot, packages, package_name, inputs=None):
        robot.cli('new', package_name)
        robot.cd(package_name)
        robot.write_file('README', package_name)
        robot.write_file('output/README', package_name)
        self._add_inputs(robot, inputs)
        repo = self.repo(robot)
        with robot.environment:
            packages[package_name] = repo.store(Workspace('.'), TS1)
        robot.cd('..')
        robot.cli('nuke', package_name)
        return package_name

    def _add_inputs(self, robot, inputs):
        inputs = inputs or {}
        for name in inputs:
            robot.cli('input', 'add', name, inputs[name])

    def pkg_a(self, robot, packages):
        return self._new_package(robot, packages, 'pkg_a')

    def pkg_b(self, robot, packages):
        return self._new_package(robot, packages, 'pkg_b')

    def _pkg_with_history(self, robot, repo, package_name, uuid):
        def make_package(timestamp):
            with TempDir() as tempdir_obj:
                workspace_dir = os.path.join(tempdir_obj.path, package_name)
                ws = Workspace(workspace_dir)
                ws.create(uuid)
                sentinel_file = ws.directory / 'sentinel-{}'.format(timestamp)
                tech.fs.write_file(sentinel_file, timestamp)
                repo.store(ws, timestamp)
                tech.fs.rmtree(workspace_dir)

        with robot.environment:
            add_translation(package_name, uuid)
            make_package(TS1)
            make_package(TS2)
        return package_name

    def pkg_with_history(self, robot, repo):
        return self._pkg_with_history(
            robot, repo, 'pkg_with_history', 'UUID:pkg_with_history')

    def pkg_with_inputs(self, robot, packages, pkg_a, pkg_b):
        inputs = dict(input_a=pkg_a, input_b=pkg_b)
        return self._new_package(robot, packages, 'pkg_with_inputs', inputs)


class Test_package_with_history(TestCase, PackageFixtures):

    # tests
    def test_develop_by_name(self, robot, pkg_a):
        robot.cli('develop', pkg_a)

        self.assertTrue(Workspace(robot.cwd / pkg_a).is_valid)
        self.assertThat(robot.cwd / pkg_a / 'README', FileContains(pkg_a))

    def test_develop_missing_package(self, robot, pkg_a):
        robot.cli('repo', 'forget', 'repo')
        try:
            robot.cli('develop', pkg_a)
        except SystemExit:
            self.assertThat(robot.stderr, Contains('Package'))
            self.assertThat(robot.stderr, Contains('not found'))
        else:
            self.fail('develop should have exited on missing package')

    def assert_develop_version(self, robot, pkg_spec, timestamp):
        assert pkg_spec.startswith('pkg_with_history')
        robot.cli('develop', pkg_spec)
        self.assertThat(
            robot.cwd / 'pkg_with_history' / 'sentinel-' + timestamp,
            FileExists())

    def test_develop_without_version(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history', TS2)

    def test_develop_without_offset(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history@', TS2)

    def test_develop_with_offset(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history@-1', TS1)

    def test_develop_w_version_wo_offset(self, robot, pkg_with_history):
        self.assert_develop_version(robot, 'pkg_with_history@' + TS1, TS1)

    def test_develop_available_matches_to_version_are_less_than_offset(
            self, robot, pkg_with_history):
        self.assert_develop_version(
            robot, 'pkg_with_history@{}-1'.format(TS2), TS2)


class Test_input_commands(TestCase, PackageFixtures):

    def assert_mounted(self, robot, input_name, package_name):
        self.assertThat(
            robot.cwd / 'input' / input_name / 'README',
            FileContains(package_name))

    # tests

    def test_input_commands(self, robot, pkg_with_history):
        # nextpkg with input1 as datapkg1
        robot.cli('new', 'nextpkg')
        robot.cd('nextpkg')
        robot.cli('input', 'add', 'input1', 'pkg_with_history@' + TS1)
        robot.cli('pack')
        robot.cd('..')
        robot.cli('nuke', 'nextpkg')

        robot.cli('develop', 'nextpkg')
        robot.cd('nextpkg')
        assert not os.path.exists(robot.cwd / 'input/input1')

        robot.cli('input', 'load')
        assert os.path.exists(robot.cwd / 'input/input1')

        robot.cli('input', 'add', 'input2', 'pkg_with_history')
        assert os.path.exists(robot.cwd / 'input/input2')

        robot.cli('input', 'delete', 'input1')
        assert not os.path.exists(robot.cwd / 'input/input1')

        # no-op load do not crash
        robot.cli('input', 'load')

        robot.cli('status')

    def test_update_unmounted_input_with_explicit_package(
            self, robot, pkg_with_inputs, pkg_a, pkg_b):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)

        assert not Workspace(robot.cwd).is_mounted('input_b')

        robot.cli('input', 'update', 'input_b', pkg_a)
        self.assert_mounted(robot, 'input_b', pkg_a)

        robot.cli('status')
        self.assertThat(robot.stdout, Not(Contains(pkg_b)))


class Test_status(TestCase, PackageFixtures):

    # tests

    def test(self, robot, packages, pkg_with_inputs, pkg_a):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)
        robot.cli('status')

        self.assertThat(robot.stdout, Contains(pkg_with_inputs))
        self.assertThat(robot.stdout, Contains(pkg_a))

        pkg_a = packages[pkg_a]
        pkg_with_inputs = packages[pkg_with_inputs]
        self.assertThat(robot.stdout, Not(Contains(pkg_with_inputs.uuid)))
        self.assertThat(robot.stdout, Not(Contains(pkg_a.uuid)))
        self.assertThat(robot.stdout, Contains(pkg_a.timestamp_str))
        self.assertThat(robot.stdout, Not(Contains(pkg_a.version)))

    def test_verbose(self, robot, packages, pkg_with_inputs, pkg_a):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)
        robot.cli('status', '-v')

        self.assertThat(robot.stdout, Contains(pkg_with_inputs))
        self.assertThat(robot.stdout, Contains(pkg_a))

        pkg_a = packages[pkg_a]
        pkg_with_inputs = packages[pkg_with_inputs]
        self.assertThat(robot.stdout, Contains(pkg_with_inputs.uuid))
        self.assertThat(robot.stdout, Contains(pkg_a.uuid))
        self.assertThat(robot.stdout, Contains(pkg_a.timestamp_str))
        self.assertThat(robot.stdout, Contains(pkg_a.version))

    def test_no_translations(self, robot, packages, pkg_with_inputs, pkg_a):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)
        robot.cause_amnesia()
        robot.cli('status')

        self.assertThat(robot.stdout, Not(Contains(pkg_with_inputs)))
        self.assertThat(robot.stdout, Not(Contains(pkg_a)))

        pkg_a = packages[pkg_a]
        pkg_with_inputs = packages[pkg_with_inputs]
        self.assertThat(robot.stdout, Contains(pkg_with_inputs.uuid))
        self.assertThat(robot.stdout, Contains(pkg_a.uuid))
        self.assertThat(robot.stdout, Not(Contains(pkg_a.timestamp_str)))
        self.assertThat(robot.stdout, Contains(pkg_a.version))

    def test_verbose2(self, robot, packages, pkg_with_inputs, pkg_a):
        robot.cli('develop', pkg_with_inputs)
        robot.cd(pkg_with_inputs)
        robot.cause_amnesia()
        robot.cli('status', '--verbose')

        self.assertThat(robot.stdout, Not(Contains(pkg_with_inputs)))
        self.assertThat(robot.stdout, Not(Contains(pkg_a)))

        pkg_a = packages[pkg_a]
        pkg_with_inputs = packages[pkg_with_inputs]
        self.assertThat(robot.stdout, Contains(pkg_with_inputs.uuid))
        self.assertThat(robot.stdout, Contains(pkg_a.uuid))
        self.assertThat(robot.stdout, Not(Contains(pkg_a.timestamp_str)))
        self.assertThat(robot.stdout, Contains(pkg_a.version))
