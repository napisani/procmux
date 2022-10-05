from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, List

from app.config import ProcessConfig


class FocusWidget(Enum):
    SIDE_BAR_FILTER = auto()
    SIDE_BAR_SELECT = auto()
    TERMINAL = auto()
    TERMINAL_COMMAND_INPUTS = auto()
    DOCS = auto()


@dataclass
class Process:
    index: int
    config: ProcessConfig
    name: str
    running: bool = False
    scroll_mode: bool = False


@dataclass(frozen=True)
class KeybindingDocumentation:
    label: str
    help: str
    should_display: Callable[[], bool] = field(default_factory=lambda: lambda: True)


@dataclass(frozen=True)
class FocusTarget:
    widget: FocusWidget
    element: Any
    keybinding_help: List[KeybindingDocumentation] = field(default_factory=lambda: [])
