'''
We are responsible to store (and retrieve) packages.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function


import os

from .pkg.archive import Archive
from .import tech
Path = tech.fs.Path

from .tech import persistence


ENV_REPOS = 'repositories'
REPO_NAME = 'name'
REPO_LOCATION = 'directory'


class Environment:

    def __init__(self, filename):
        self.filename = filename
        self._content = {}

    def load(self):
        with open(self.filename, 'rb') as f:
            self._content = persistence.load(f)

    def save(self):
        with open(self.filename, 'wb') as f:
            persistence.dump(self._content, f)

    def get_repos(self):
        for repo_spec in self._content.get(ENV_REPOS, ()):
            repo = Repository(
                repo_spec.get(REPO_NAME),
                repo_spec.get(REPO_LOCATION))
            yield repo

    def set_repos(self, repos):
        self._content[ENV_REPOS] = [
            {
                REPO_NAME: repo.name,
                REPO_LOCATION: repo.location
            }
            for repo in repos]


env = None


def initialize(config_dir):
    try:
        os.makedirs(config_dir)
    except OSError:
        assert os.path.isdir(config_dir)
    global env
    env_path = Path(config_dir) / 'env.json'
    env = Environment(env_path)
    if os.path.exists(env_path):
        env.load()


class Repository(object):
    # TODO: user maintained directory hierarchy

    def __init__(self, name=None, location=None):
        self.location = location
        self.name = name

    @property
    def directory(self):
        '''
        Location as a Path.

        Valid only for local repositories.
        '''
        return Path(self.location)

    def find_packages(self, uuid, version=None):
        # -> [Package]
        try:
            names = os.listdir(self.directory)
        except OSError:
            # ignore deleted repository
            # XXX - we should log this problem
            names = []

        for name in names:
            candidate = self.directory / name
            try:
                package = Archive(candidate)
                if package.uuid == uuid:
                    if version in (None, package.version):
                        yield package
            except:
                # ignore invalid packages
                # XXX - we should log them
                pass

    def store(self, workspace, timestamp):
        # -> Package
        zipfilename = (
            self.directory / (
                '{package}_{timestamp}.zip'
                .format(
                    package=workspace.package_name,
                    timestamp=timestamp)))
        workspace.pack(zipfilename, timestamp=timestamp)
        return Archive(zipfilename)


def get(name):
    '''
    Return repository having :name or None.
    '''
    for repo in env.get_repos:
        if repo.name == name:
            return repo


def is_known(name):
    return get(name) is not None


def get_all():
    return env.get_repos()


def add(name, directory):
    repos = list(env.get_repos())
    # check unique repo
    for repo in repos:
        if repo.name == name:
            raise ValueError(
                'Repository with name {} already exists'.format(name))
        if repo.location == directory:
            raise ValueError(
                'Repository with location {} already exists'.format(location))

    env.set_repos(repos + [Repository(name, directory)])
    env.save()


def forget(name):
    env.set_repos(
        repo
        for repo in env.get_repos()
        if repo.name != name)
    env.save()


def get_package(uuid, version):
    for repo in get_all():
        for package in repo.find_packages(uuid, version):
            return package
    raise LookupError('Package {} {} not found'.format(uuid, version))
