'''
layout of beads
'''

from . import tech

Path = tech.fs.Path


class Archive:

    META = Path('meta')
    CODE = Path('code')
    DATA = Path('data')

    BEAD_META = META / 'bead'
    MANIFEST = META / 'manifest'


class Workspace:

    INPUT = Path('input')
    OUTPUT = Path('output')
    TEMP = Path('temp')
    META = Path('.bead-meta')

    BEAD_META = META / 'bead'
