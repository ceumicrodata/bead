import contextlib
import os
import fixtures
from tracelog import TRACELOG

from bead import tech

from bead.test import TempDir, CaptureStdout, CaptureStderr, chdir
from .main import run
from .environment import Environment


@contextlib.contextmanager
def environment(robot):
    '''
    Context manager - enable running code in the context of the robot.
    '''
    with fixtures.EnvironmentVariable('HOME', robot.home):
        with chdir(robot.cwd):
            try:
                # FIXME: robot: environment file should be built by a function in environment
                yield Environment(robot.config_dir / 'env.json')
            except BaseException as e:
                robot.retval = e
                raise


class Robot(fixtures.Fixture):
    '''
    Represents a fake user.

    All operations are isolated from the test runner user's environment.
    They work in a dedicated environment with temporary home, config
    and working directories.
    '''

    def setUp(self):
        super(Robot, self).setUp()
        self.base_dir = self.useFixture(TempDir()).path
        TRACELOG('makedirs', self.home)
        os.makedirs(self.home)
        self.cd(self.home)

    def cleanUp(self):
        super(Robot, self).cleanUp()
        self.base_dir = None

    @property
    def config_dir(self):
        return self.base_dir / 'config'

    @property
    def home(self):
        return self.base_dir / 'home'

    def _path(self, path):
        '''
        Convert relative paths to absolute paths
        '''
        if os.path.isabs(path):
            return path
        else:
            return tech.fs.Path(os.path.normpath(self.cwd / path))

    def cd(self, dir):
        '''
        Change to directory
        '''
        self.cwd = self._path(dir)
        TRACELOG(dir, realdir=self.cwd)
        assert os.path.isdir(self.cwd)

    @property
    def environment(self):
        '''
        Context manager - enable running code in the context of this robot.
        '''
        return environment(self)

    def cli(self, *args):
        '''
        Imitate calling the command line tool with the given args
        '''
        TRACELOG(*args)
        with self.environment:
            with CaptureStdout() as stdout, CaptureStderr() as stderr:
                try:
                    self.retval = run(''.__class__(self.config_dir), args)
                except BaseException as e:
                    TRACELOG(EXCEPTION=e)
                    raise
                finally:
                    self.stdout = stdout.text
                    self.stderr = stderr.text
                    #
                    if self.stdout:
                        TRACELOG(STDOUT=self.stdout)
                    if self.stderr:
                        TRACELOG(STDERR=self.stderr)

    def ls(self, directory=None):
        directory = self._path(directory or self.cwd)
        return [
            directory / filename
            for filename in os.listdir(directory)]

    def write_file(self, path, content):
        assert not os.path.isabs(path)
        TRACELOG(path, content, realpath=self.cwd / path)
        tech.fs.write_file(self.cwd / path, content)

    def reset(self):
        '''
        Forget all boxes by removing the user's config.

        All other files, workspaces remain available.
        '''
        TRACELOG('rmtree', self.config_dir)
        tech.fs.rmtree(self.config_dir)
