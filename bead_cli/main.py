import sys

import appdirs
from .cmdparse import Parser, Command

from bead.tech.fs import Path
from . import workspace
from . import input
from . import box
from . import PACKAGE, VERSION


class CmdVersion(Command):
    '''
    Show program version
    '''

    def run(self, args):
        print(f'{PACKAGE} version {VERSION}')


def make_argument_parser(defaults):
    parser = Parser.new(defaults)
    (parser
        .commands(
            'new',
            workspace.CmdNew,
            'Create and initialize new workspace directory with a new bead.',

            'develop',
            workspace.CmdDevelop,
            'Create workspace from specified bead.',

            'save',
            workspace.CmdSave,
            'Save workspace in a box.',

            'status',
            workspace.CmdStatus,
            'Show workspace information.',

            'nuke',
            workspace.CmdNuke,
            'Delete workspace.',

            'web',
            workspace.CmdWeb,
            'Visualize connections to other beads.',

            'version',
            CmdVersion,
            'Show program version.'))

    (parser
        .group('input', 'Manage data loaded from other beads')
        .commands(
            'add',
            input.CmdAdd,
            'Define dependency and load its data.',

            'delete',
            input.CmdDelete,
            'Forget all about an input.',

            'update',
            input.CmdUpdate,
            'Update input[s] to newest version or defined bead.',

            'load',
            input.CmdLoad,
            'Load data from already defined dependency.',

            'unload',
            input.CmdUnload,
            'Unload input data.',))

    (parser
        .group('box', 'Manage bead boxes')
        .commands(
            'add',
            box.CmdAdd,
            'Define a box.',

            'list',
            box.CmdList,
            'Show known boxes.',

            'forget',
            box.CmdForget,
            'Forget a known box.'))

    return parser


def run(config_dir, argv):
    parser_defaults = dict(config_dir=Path(config_dir))
    parser = make_argument_parser(parser_defaults)
    return parser.dispatch(argv)


def main():
    config_dir = appdirs.user_config_dir(
        PACKAGE + '-6a4d9d98-8e64-4a2a-b6c2-8a753ea61daf')
    try:
        retval = run(config_dir, sys.argv[1:])
    except BaseException:
        # TODO: ask the user to report the exception?!
        raise
    sys.exit(retval)


if __name__ == '__main__':
    main()
