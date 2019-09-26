from bead.test import TempDir
from tracelog import TRACELOG

import os
import warnings
import zipfile

from bead.workspace import Workspace
from bead import layouts
from bead import tech
from .test_robot import Robot


# timestamps
TS1 = '20150901T151015000001+0200'
TS2 = '20150901T151016000002+0200'
TS3 = '20150901T151017000003+0200'
TS4 = '20150901T151018000004+0200'
TS5 = '20150901T151019000005+0200'
TS_LAST = TS5


class RobotAndBeads(object):

    # fixtures
    def robot(self):
        '''
        I am a robot user with a box
        '''
        robot = self.useFixture(Robot())
        box_dir = robot.cwd / 'box'
        os.makedirs(box_dir)
        robot.cli('box', 'add', 'box', box_dir)
        return robot

    def box(self, robot):
        with robot.environment as env:
            return env.get_box('box')

    def beads(self):
        return {}

    def _new_bead(self, robot, beads, bead_name, inputs=None):
        robot.cli('new', bead_name)
        robot.cd(bead_name)
        robot.write_file('README', bead_name)
        robot.write_file('output/README', bead_name)
        self._add_inputs(robot, inputs)
        box = self.box(robot)
        with robot.environment:
            TRACELOG('store', robot.cwd, TS1, 'to', box.location)
            beads[bead_name] = box.store(Workspace('.'), TS1)
        robot.cd('..')
        robot.cli('nuke', bead_name)
        return bead_name

    def _add_inputs(self, robot, inputs):
        inputs = inputs or {}
        for name in inputs:
            robot.cli('input', 'add', name, inputs[name])

    def bead_a(self, robot, beads):
        return self._new_bead(robot, beads, 'bead_a')

    def bead_b(self, robot, beads):
        return self._new_bead(robot, beads, 'bead_b')

    def hacked_bead(self, robot, beads):
        hacked_bead_path = self.new_temp_dir() / 'hacked_bead.zip'
        workspace_dir = self.new_temp_dir() / 'hacked_bead'
        ws = Workspace(workspace_dir)
        ws.create('hacked-kind')
        tech.fs.write_file(ws.directory / 'code', 'code')
        tech.fs.write_file(ws.directory / 'output/README', 'README')
        ws.pack(hacked_bead_path, TS1, comment='hacked bead')
        with zipfile.ZipFile(hacked_bead_path, 'a') as z:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                # this would cause a warning from zipfile for duplicate
                # name in zip file (which is perfectly valid, though hacky)
                z.writestr(layouts.Archive.CODE / 'code', 'HACKED')
                z.writestr(layouts.Archive.DATA / 'README', 'HACKED')
        return hacked_bead_path

    def _bead_with_history(self, robot, box, bead_name, bead_kind):
        def make_bead(timestamp):
            with TempDir() as tempdir_obj:
                workspace_dir = os.path.join(tempdir_obj.path, bead_name)
                ws = Workspace(workspace_dir)
                ws.create(bead_kind)
                sentinel_file = ws.directory / f'sentinel-{timestamp}'
                tech.fs.write_file(sentinel_file, timestamp)
                tech.fs.write_file(ws.directory / 'output/README', timestamp)
                box.store(ws, timestamp)
                tech.fs.rmtree(workspace_dir)

        with robot.environment:
            make_bead(TS1)
            make_bead(TS2)
            make_bead(TS3)
            make_bead(TS4)
            make_bead(TS5)
        return bead_name

    def bead_with_history(self, robot, box):
        return self._bead_with_history(
            robot, box, 'bead_with_history', 'KIND:bead_with_history')

    def bead_with_inputs(self, robot, beads, bead_a, bead_b):
        inputs = dict(input_a=bead_a, input_b=bead_b)
        return self._new_bead(robot, beads, 'bead_with_inputs', inputs)
