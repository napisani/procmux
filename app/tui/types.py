from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from app.config import ProcessConfig


class FocusWidget(Enum):
    SIDE_BAR_FILTER = auto()
    SIDE_BAR_SELECT = auto()
    TERMINAL = auto()
    TERMINAL_COMMAND_INPUTS = auto()
    DOCS = auto()


@dataclass(frozen=True)
class FocusTarget:
    widget: FocusWidget
    element: Any


@dataclass(frozen=True)
class KeybindingDocumentation:
    label: str
    help: str


@dataclass
class Process:
    index: int
    config: ProcessConfig
    name: str
    running: bool = False
    scroll_mode: bool = False
