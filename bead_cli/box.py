import os

from .cmdparse import Command
from .common import OPTIONAL_ENV


class CmdAdd(Command):
    '''
    Define a box.
    '''

    def declare(self, arg):
        arg('name')
        arg('directory')
        arg(OPTIONAL_ENV)

    def run(self, args):
        '''
        Define a box.
        '''
        name, directory = args.name, args.directory
        env = args.get_env()

        if not os.path.isdir(directory):
            print(f'ERROR: "{directory}" is not an existing directory!')
            return
        location = os.path.abspath(directory)
        try:
            env.add_box(name, location)
            env.save()
            print(f'Will remember box {name}')
        except ValueError as e:
            print('ERROR:', *e.args)
            print('Check the parameters: both name and directory must be unique!')


class CmdList(Command):
    '''
    List boxes.
    '''

    def declare(self, arg):
        arg(OPTIONAL_ENV)

    def run(self, args):
        boxes = args.get_env().get_boxes()

        def print_box(box):
            print(f'{box.name}: {box.location}')
        if boxes:
            # XXX: list command: use tabulate?
            print('Boxes:')
            print('-------------')
            for box in boxes:
                print_box(box)
        else:
            print('There are no defined boxes')


class CmdForget(Command):
    '''
    Remove the named box from the boxes known by the tool.
    '''

    def declare(self, arg):
        arg('name')
        arg(OPTIONAL_ENV)

    def run(self, args):
        name = args.name
        env = args.get_env()

        if env.is_known_box(name):
            env.forget_box(name)
            env.save()
            print(f'Box "{name}" is forgotten')
        else:
            print(f'WARNING: no box defined with "{name}"')
