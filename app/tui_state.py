from dataclasses import dataclass, field
from enum import auto, Enum
from typing import List, Optional
from app.exec import TerminalManager


class FocusWidget(Enum):
    SIDE_BAR = auto()
    TERMINAL = auto()


@dataclass
class TUIState:
    selected_process_idx: Optional[int] = None
    process_name_list: List[str] = field(default_factory=lambda: [])
    process_status_list: List[bool] = field(default_factory=lambda: [])
    terminal_managers: List[TerminalManager] = field(default_factory=lambda: [])
    focus: FocusWidget = FocusWidget.SIDE_BAR
