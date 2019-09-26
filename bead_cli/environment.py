'''
User specific environment
'''

from bead.box import Box
from bead.tech import persistence
import os

ENV_BOXES = 'boxes'
BOX_NAME = 'name'
BOX_LOCATION = 'directory'


class Environment:

    def __init__(self, filename):
        self.filename = filename
        self._content = {}
        if os.path.exists(self.filename):
            self.load()

    def load(self):
        with open(self.filename, 'r') as f:
            self._content = persistence.load(f)

    def save(self):
        with open(self.filename, 'w') as f:
            persistence.dump(self._content, f)

    def get_boxes(self):
        def box(box_spec):
            return Box(
                box_spec.get(BOX_NAME),
                box_spec.get(BOX_LOCATION))
        return [box(spec) for spec in self._content.get(ENV_BOXES, ())]

    def set_boxes(self, boxes):
        self._content[ENV_BOXES] = [
            {
                BOX_NAME: box.name,
                BOX_LOCATION: box.location
            }
            for box in boxes]

    def add_box(self, name, directory):
        boxes = self.get_boxes()
        # check unique box
        for box in boxes:
            if box.name == name:
                raise ValueError(f'Box with name {name} already exists')
            if box.location == directory:
                raise ValueError(
                    f'Box with location {box.location} already exists')

        self.set_boxes(boxes + [Box(name, directory)])

    def forget_box(self, name):
        self.set_boxes(
            box
            for box in self.get_boxes()
            if box.name != name)

    def get_box(self, name):
        '''
        Return box having :name or None.
        '''
        for box in self.get_boxes():
            if box.name == name:
                return box

    def is_known_box(self, name):
        return self.get_box(name) is not None

    def get_bead(self, kind, content_id):
        for box in self.get_boxes():
            try:
                return box.get_bead(kind, content_id)
            except LookupError:
                pass
        raise LookupError(f'Bead {kind}/{content_id} not found')
