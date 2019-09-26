import os
import sys

from bead.workspace import Workspace
from bead import spec as bead_spec
from bead.archive import Archive
from bead import box as bead_box
from . import arg_help
from . import arg_metavar
from bead.tech.timestamp import time_from_user, parse_iso8601
from .environment import Environment


TIME_LATEST = parse_iso8601('9999-12-31')

ERROR_EXIT = 1


def die(msg):
    sys.stderr.write('ERROR: ')
    sys.stderr.write(msg)
    sys.stderr.write('\n')
    sys.exit(ERROR_EXIT)


def warning(msg):
    sys.stderr.write('WARNING: ')
    sys.stderr.write(msg)
    sys.stderr.write('\n')


def OPTIONAL_WORKSPACE(parser):
    '''
    Define `workspace` as option, defaulting to current directory
    '''
    parser.arg(
        '--workspace', '-w', metavar=arg_metavar.WORKSPACE,
        type=Workspace, default=Workspace.for_current_working_directory(),
        help=arg_help.WORKSPACE)


class get_env:
    '''
    Make an Environment when called.

    It will also create a missing config directory and provides a meaningful
    text when used as default for an argparse argument.
    '''

    def __init__(self, config_dir):
        self.config_dir = config_dir

    def __call__(self):
        config_dir = self.config_dir
        try:
            os.makedirs(config_dir)
        except OSError:
            assert os.path.isdir(config_dir)
        return Environment(config_dir / 'env.json')

    def __repr__(self):
        return f'Environment at {self.config_dir}'


def OPTIONAL_ENV(parser):
    '''
    Define `env` as option, defaulting to environment config in user's home directory
    '''
    config_dir = parser.defaults['config_dir']
    parser.arg(
        '--env', '--environment', metavar=arg_metavar.ENV,
        dest='get_env',
        type=get_env, default=get_env(config_dir),
        help=arg_help.ENV)


class DefaultArgSentinel(object):
    '''
    I am a sentinel for default values.

    I.e. If you see me, it means that you got the default value.

    I also provide human sensible description for the default value.
    '''

    def __init__(self, description):
        self.description = description

    def __repr__(self):
        return self.description


def BEAD_TIME(parser):
    parser.arg('-t', '--time', dest='bead_time', type=time_from_user, default=TIME_LATEST)


def BEAD_OFFSET(parser):
    parser.arg('-N', '--next', dest='bead_offset', action='store_const', const=1, default=0)
    parser.arg('-P', '--prev', '--previous', dest='bead_offset', action='store_const', const=-1)


def arg_bead_ref_base(nargs, default):
    '''
    Declare bead_ref_base argument - either a name or a file or something special
    '''
    def declare(parser):
        parser.arg(
            'bead_ref_base', metavar=arg_metavar.BEAD_REF, help=arg_help.BEAD_REF,
            nargs=nargs, type=str, default=default)
    return declare


def BEAD_REF_BASE_defaulting_to(name):
    return arg_bead_ref_base(nargs='?', default=name)


BEAD_REF_BASE = arg_bead_ref_base(nargs=None, default=None)


def resolve_bead(env, bead_ref_base, time):
    # prefer exact file name over box search
    if os.path.isfile(bead_ref_base):
        return Archive(bead_ref_base)

    # not a file - try box search
    unionbox = bead_box.UnionBox(env.get_boxes())

    return unionbox.get_at(bead_spec.BEAD_NAME_GLOB, bead_ref_base, time)


def verify_with_feedback(archive):
    print(f'Verifying archive {archive.archive_filename} ...', end='', flush=True)
    is_valid = archive.is_valid
    if is_valid:
        print(' OK', flush=True)
    else:
        print(' DAMAGED!', flush=True)
    return is_valid
