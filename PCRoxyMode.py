from enum import Enum


class PCRoxyMode(Enum):
    OBSERVER = 1
    MODIFIER = 2

    def isSafe(self) -> bool:
        return self in [PCRoxyMode.OBSERVER]
