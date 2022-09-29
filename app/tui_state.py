from dataclasses import dataclass, field
from enum import auto, Enum
from typing import Dict, List, Optional
from app.exec import TerminalManager


class FocusWidget(Enum):
    SIDE_BAR_FILTER = auto()
    SIDE_BAR_SELECT = auto()
    TERMINAL = auto()
    DOCS = auto()


@dataclass
class TUIState:
    _process_name_to_idx: Optional[Dict[str, int]] = None
    selected_process_idx: Optional[int] = None
    process_name_list: List[str] = field(default_factory=lambda: [])
    process_status_list: List[bool] = field(default_factory=lambda: [])
    terminal_managers: List[TerminalManager] = field(default_factory=lambda: [])
    zoomed_in: bool = False
    docs_open: bool = False
    quitting: bool = False

    @property
    def selected_process_terminal_manager(self) -> Optional[TerminalManager]:
        if self.selected_process_idx is not None and self.selected_process_idx > -1:
            return self.terminal_managers[self.selected_process_idx]
        return None

    @property
    def is_selected_process_running(self) -> bool:
        return self.selected_process_terminal_manager.is_running() \
            if self.selected_process_terminal_manager else False

    @property
    def selected_process_has_terminal(self) -> bool:
        return \
            self.selected_process_terminal_manager.get_terminal() is not None \
            if self.selected_process_terminal_manager else False

    @property
    def has_running_processes(self) -> bool:
        for tm in self.terminal_managers:
            if tm.is_running():
                return True
        return False

    def get_process_index_by_name(self, proc_name):
        if not self._process_name_to_idx:
            self._process_name_to_idx = {name: idx for idx, name in enumerate(self.process_name_list)}
        idx = self._process_name_to_idx[proc_name]
        return idx

    def get_terminal_manager_by_name(self, proc_name):
        idx = self.get_process_index_by_name(proc_name)
        return self.terminal_managers[idx]
