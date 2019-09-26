import os
import sys
import time
import subprocess
import webbrowser

from bead import tech
from bead.workspace import Workspace
from bead import layouts

from bead.box import UnionBox

from .cmdparse import Command
from .common import die, warning
from .common import DefaultArgSentinel
from .common import OPTIONAL_WORKSPACE, OPTIONAL_ENV
from .common import BEAD_REF_BASE, BEAD_TIME, resolve_bead
from .common import verify_with_feedback
from . import arg_metavar
from . import arg_help
from . import web

timestamp = tech.timestamp.timestamp


def assert_may_be_valid_name(name):
    '''
    Refuse bead names that are non cross platform file-system compatible
    '''
    valid_syntax = (
        name
        and os.path.sep not in name
        and '/' not in name
        and '\\' not in name
        and ':' not in name
    )
    if not valid_syntax:
        die(f'Invalid name "{name}"')


class CmdNew(Command):
    '''
    Create and initialize new workspace directory with a new bead.
    '''

    def declare(self, arg):
        arg('workspace', type=Workspace, metavar=arg_metavar.WORKSPACE,
            help='bead and directory to create')

    def run(self, args):
        workspace = args.workspace
        assert_may_be_valid_name(workspace.name)
        # FIXME: die with message when directory already exists

        kind = tech.identifier.uuid()
        workspace.create(kind)
        print(f'Created {workspace.name}')


def WORKSPACE_defaulting_to(default_workspace):
    def opt_workspace(parser):
        parser.arg(
            'workspace', nargs='?', type=Workspace,
            default=default_workspace,
            metavar=arg_metavar.WORKSPACE, help=arg_help.WORKSPACE)
    return opt_workspace


USE_THE_ONLY_BOX = DefaultArgSentinel(
    'if there is exactly one box,' +
    ' store there, otherwise it MUST be specified')


class CmdSave(Command):
    '''
    Save workspace in a box.
    '''

    def declare(self, arg):
        arg('box_name', nargs='?', default=USE_THE_ONLY_BOX, type=str,
            metavar=arg_metavar.BOX, help=arg_help.BOX)
        arg(OPTIONAL_WORKSPACE)
        arg(OPTIONAL_ENV)

    def run(self, args):
        box_name = args.box_name
        workspace = args.workspace
        env = args.get_env()
        assert_valid_workspace(workspace)
        # XXX: (usability) save - support saving directly to a directory outside of workspace
        if box_name is USE_THE_ONLY_BOX:
            boxes = env.get_boxes()
            if not boxes:
                warning('No boxes have been defined')
                beadbox = os.path.expanduser('~/BeadBox')
                sys.stderr.write(
                    f'Creating and using a new one with name `home` and location {beadbox}')
                tech.fs.ensure_directory(beadbox)
                env.add_box('home', beadbox)
                env.save()
                # continue with newly created box
                boxes = env.get_boxes()
                assert len(boxes) == 1
            if len(boxes) > 1:
                die(
                    'BOX parameter is not optional!\n' +
                    '(more than one boxes exists)')
            box = boxes[0]
        else:
            box = env.get_box(box_name)
            if box is None:
                die(f'Unknown box: {box_name}')
        box.store(workspace, timestamp())
        print('Successfully stored bead.')


DERIVE_FROM_BEAD_NAME = DefaultArgSentinel('derive one from bead name')


class CmdDevelop(Command):
    '''
    Unpack a bead as a source tree.

    Bead directory layout is created, but only the source files are
    extracted.
    '''

    def declare(self, arg):
        arg(BEAD_REF_BASE)
        arg(BEAD_TIME)
        arg(WORKSPACE_defaulting_to(DERIVE_FROM_BEAD_NAME))
        arg('-x', '--extract-output', dest='extract_output',
            default=False, action='store_true',
            help='Extract output data as well (normally it is not needed!).')
        arg(OPTIONAL_ENV)

    def run(self, args):
        extract_output = args.extract_output
        env = args.get_env()
        try:
            bead = resolve_bead(env, args.bead_ref_base, args.bead_time)
        except LookupError:
            die('Bead not found!')
        is_valid = verify_with_feedback(bead)
        if not is_valid:
            die('Bead is found but damaged')
        if args.workspace is DERIVE_FROM_BEAD_NAME:
            workspace = Workspace(bead.name)
        else:
            workspace = args.workspace

        bead.unpack_to(workspace)
        assert workspace.is_valid

        if extract_output:
            output_directory = workspace.directory / layouts.Workspace.OUTPUT
            bead.unpack_data_to(output_directory)

        print(f'Extracted source into {workspace.directory}')
        # XXX: try to load smaller inputs?
        if workspace.inputs:
            print('Input data not loaded, update if needed and load manually')


def assert_valid_workspace(workspace):
    if not workspace.is_valid:
        die(f'{workspace.directory} is not a valid workspace')


def print_inputs(env, workspace, verbose):
    assert_valid_workspace(workspace)
    inputs = sorted(workspace.inputs)

    if inputs:
        boxes = env.get_boxes()

        print('Inputs:')
        for input in inputs:
            print('input/' + input.name)
            print('\tFreeze time:', input.timestamp_str)
            print('\tName[s]:')
            has_name = False
            for box in boxes:
                (
                    exact_match, best_guess, best_guess_timestamp, names
                ) = box.find_names(input.kind, input.content_id, input.timestamp)
                #
                has_name = has_name or exact_match or best_guess or names
                if exact_match:
                    print(f'\t * -r {box.name} {exact_match}')
                    names.remove(exact_match)
                elif best_guess:
                    print(f'\t ? -r {box.name} {best_guess}')
                    names.remove(best_guess)
                for name in sorted(names):
                    print(f'\t [-r {box.name} {name}]')
            if verbose or not has_name:
                print('\tBead kind:', input.kind)
                print('\tContent id:', input.content_id)

        print('')
        unloaded = [
            input.name
            for input in inputs
            if not workspace.is_loaded(input.name)]
        if unloaded:
            print('These inputs are not loaded:')
            unloaded_list = '\t- ' + '\n\t- '.join(unloaded)
            print(unloaded_list.expandtabs(2))
            print('You can "load" or "update" them manually.')
    else:
        print('No inputs defined')


class CmdStatus(Command):
    '''
    Show workspace status - name of bead, inputs and their unpack status.
    '''

    def declare(self, arg):
        arg(OPTIONAL_WORKSPACE)
        arg('-v', '--verbose', default=False, action='store_true',
            help='show more detailed information')
        arg(OPTIONAL_ENV)

    def run(self, args):
        workspace = args.workspace
        verbose = args.verbose
        env = args.get_env()
        # TODO: use a template and render it with passing in all data
        kind_needed = verbose
        if workspace.is_valid:
            print(f'Bead Name: {workspace.name}')
            if kind_needed:
                print(f'Bead kind: {workspace.kind}')
            print()
            print_inputs(env, workspace, verbose)
        else:
            warning(f'Invalid workspace ({workspace.directory})')


class CmdNuke(Command):
    '''
    Delete the workspace, inluding data, code and documentation.
    '''

    def declare(self, arg):
        arg(WORKSPACE_defaulting_to(Workspace.for_current_working_directory()))

    def run(self, args):
        workspace = args.workspace
        assert_valid_workspace(workspace)
        directory = workspace.directory
        # on non-posix systems (Windows) it might happen, that we can not remove
        # the directory we are in -> ignore errors
        tech.fs.rmtree(directory, ignore_errors=os.name != 'posix')
        print(f'Deleted workspace {directory}')


class CmdWeb(Command):
    '''
    Visualize connections to other beads.

    Write a GraphViz .dot file and create other representations as requested.
    '''

    def declare(self, arg):
        arg(OPTIONAL_ENV)
        arg('-o', '--output-base', default='web',
            help='File name base of generated files'
            + ' (e.g. dot file will be stored as <OUTPUT_BASE>.dot)')
        arg('--to-csv', default=False, action='store_true',
            help='Write bead meta data to files:'
            + ' <OUTPUT_BASE>-beads.csv and <OUTPUT_BASE>-inputs.csv')
        arg('--from-csv', metavar='INPUT_BASE',
            help='Load bead metadata from <INPUT_BASE>-beads.csv and <INPUT_BASE>-inputs.csv')
        arg('--svg', default=False, action='store_true',
            help="Call GraphViz's `dot` to create <OUTPUT_BASE>.svg file as well")
        arg('--png', default=False, action='store_true',
            help="Call GraphViz's `dot` to create an <OUTPUT_BASE>.png file as well")
        arg('--view', default=False, action='store_true',
            help="Open web browser with the generated SVG file (implies --svg)")
        arg('--drop-edges', default=False, action='store_true',
            help="Show only edges for the most recent beads for each kind")
        arg('names', metavar='NAME', nargs='*',
            help="Restrict output graph to these names and their inputs (default: all beads)")

    def run(self, args):
        base_file = args.output_base

        if args.from_csv:
            with open(f'{args.from_csv}_beads.csv') as beads_csv_stream:
                with open(f'{args.from_csv}_inputs.csv') as inputs_csv_stream:
                    all_beads = web.read_beads(beads_csv_stream, inputs_csv_stream)
        else:
            env = args.get_env()
            all_beads = load_all_beads(env.get_boxes())
        print(f"Loaded {len(all_beads)} beads")

        if args.to_csv:
            with open(f'{base_file}_beads.csv', 'w') as beads_csv_stream:
                with open(f'{base_file}_inputs.csv', 'w') as inputs_csv_stream:
                    web.write_beads(all_beads, beads_csv_stream, inputs_csv_stream)

        dot_weaver = web.Weaver(all_beads)
        if args.names:
            beads_to_plot = {
                bead.content_id
                for bead in dot_weaver.all_beads
                if bead.name in args.names}
            dot_weaver.restrict_to(beads_to_plot)
        do_all_edges = not args.drop_edges
        dot_str = dot_weaver.weave(do_all_edges)

        dot_file = f'{base_file}.dot'
        print(f"Creating {dot_file}")
        tech.fs.write_file(dot_file, dot_str)

        if args.png:
            png_file = f'{base_file}.png'
            print(f"Creating {png_file}")
            graphviz_dot(dot_file, png_file)

        if args.svg or args.view:
            svg_file = f'{base_file}.svg'
            print(f"Creating {svg_file}")
            graphviz_dot(dot_file, svg_file)
            if args.view:
                print(f"Viewing {svg_file}")
                webbrowser.open(svg_file)


def load_all_beads(boxes):
    columns = int(os.environ.get('COLUMNS', 80))
    all_beads = []
    load_start = time.perf_counter()
    # This UnionBox.all_beads is the meat, the rest is just user feedback for big/slow
    # environments
    for n, bead in enumerate(UnionBox(boxes).all_beads()):
        load_end = time.perf_counter()

        msg = f"\rLoaded bead {n+1} ({bead.archive_filename})"[:columns]
        msg = msg + ' ' * (columns - len(msg))
        print(msg, end="", flush=True)
        if load_end - load_start > 1:
            print(f"\nLoading took {load_end - load_start} seconds")
        all_beads.append(bead)
        load_start = time.perf_counter()
    print("\r" + " " * columns + "\r", end="")
    return all_beads


def graphviz_dot(dot_file, output_file):
    _, ext = os.path.splitext(output_file)
    filetype = ext.lstrip('.')
    cmd = ['dot', dot_file, '-o', output_file, '-T', filetype]
    subprocess.check_call(cmd)
