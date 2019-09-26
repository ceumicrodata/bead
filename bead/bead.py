from abc import ABCMeta, abstractmethod
from typing import Sequence

from .tech.timestamp import time_from_timestamp
from .meta import InputSpec


class Bead:
    '''
    Interface to metadata of a bead.
    '''

    # high level view of computation
    kind: str
    name: str
    inputs: Sequence[InputSpec]

    # frozen beads only details
    # (workspaces can fake them with recognisable values)
    content_id: str
    timestamp_str: str
    box_name: str

    # FIXME: rename Bead.timestamp* to .freeze_time*
    @property
    def timestamp(self):
        return time_from_timestamp(self.timestamp_str)

    def get_input(self, name):
        for input in self.inputs:
            if name == input.name:
                return input


class UnpackableBead(Bead):
    '''
    Provide high-level access to content of a bead.
    '''
    __metaclass__ = ABCMeta

    def unpack_to(self, workspace):
        self.unpack_code_to(workspace.directory)
        workspace.create_directories()
        self.unpack_meta_to(workspace)

    @abstractmethod
    def unpack_data_to(self, path):
        pass

    @abstractmethod
    def unpack_code_to(self, path):
        pass

    @abstractmethod
    def unpack_meta_to(self, workspace):
        pass
