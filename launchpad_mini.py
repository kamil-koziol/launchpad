from launchpad_py.launchpad import Launchpad
from enum import Enum


class LKeys(Enum):
    UP_ARROW = 1
    DOWN_ARROW = 1
    LEFT_ARROW = 1
    RIGHT_ARROW = 1


class Colors(Enum):
    NONE = 0


class LaunchpadMini(Launchpad):
    def __init__(self):
        super().__init__()

    def setup(self):
        self.Open()
        self.ButtonFlush()
        self.Reset()
