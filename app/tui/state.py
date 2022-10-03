from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from prompt_toolkit.layout import Window
from ptterm import Terminal

from app.config import ProcMuxConfig, ProcessConfig
from app.terminal_manager import TerminalManager

KeybindingDocumentation = namedtuple("KeybindingDocumentation", ["label", "help"])


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


class TUIState:
    def __init__(self, config: ProcMuxConfig):
        self.config: ProcMuxConfig = config
        self._terminal_placeholder: Window = Window(
            style=f'bg:{self.config.style.placeholder_terminal_bg_color}',
            width=self.config.style.width_100,
            height=self.config.style.height_100)
        self.process_list: List[Process] = self._create_process_list(self.config.procs)
        self.filtered_process_list: List[Process] = self.process_list
        self.selected_process: Optional[Process] = self.filtered_process_list[0] if self.filtered_process_list else None
        self.terminal_managers: Dict[int, TerminalManager] = self._create_terminal_managers(self.process_list)
        self._filter: str = ''
        self.focus_targets: List[FocusTarget] = []
        self.zoomed_in: bool = False
        self.filter_mode: bool = False
        self.docs_open: bool = False
        self.quitting: bool = False
        self.interpolating: bool = False
        self._command_form: Optional[Any] = None

    @property
    def current_terminal_manager(self) -> Optional[TerminalManager]:
        if self.selected_process:
            return self.terminal_managers.get(self.selected_process.index, None)
        return None

    @property
    def current_terminal(self) -> Union[Terminal, Window, Any]:
        if self.interpolating and self._command_form:
            return self._command_form
        if self.current_terminal_manager and self.current_terminal_manager.terminal:
            return self.current_terminal_manager.terminal
        return self._terminal_placeholder

    @property
    def has_running_processes(self) -> bool:
        for process in self.process_list:
            if process.running:
                return True
        return False

    def select_first_process(self):
        if self.filtered_process_list:
            self.selected_process = self.filtered_process_list[0]

    def set_selected_process_by_index(self, index: int):
        if self.filtered_process_list and index >= 0 and index < len(self.filtered_process_list):
            self.selected_process = self.filtered_process_list[index]

    def _create_process_list(self, process_config: Dict[str, ProcessConfig]) -> List[Process]:
        return self._sort_process_list(
            [Process(ix, pc, n) for ix, (n, pc) in enumerate(process_config.items())])

    def _sort_process_list(self, ps: List[Process]) -> List[Process]:
        if self.config.layout.sort_process_list_alpha:
            return sorted(ps, key=lambda p: p.name)
        return ps

    def _create_terminal_managers(self, process_list: List[Process]) -> Dict[int, TerminalManager]:
        tms = {}
        for process in process_list:
            tms[process.index] = TerminalManager(self.config, process.config, process.index, process.name)
        return tms

    def apply_filter(self, filter_text: str):
        self._filter = filter_text

        if not self._filter:
            self.filtered_process_list = self._sort_process_list(self.process_list)

        prefix = self.config.layout.category_search_prefix

        def filter_against_category(search_text: str, process: Process) -> bool:
            search_t = search_text[len(prefix):]
            if not process.config.categories:
                return False
            categories = {c.lower() for c in process.config.categories}
            return search_t.lower() in categories

        def filter_against_name_and_meta(search_text: str, process: Process) -> bool:
            tags = set()
            if process.config.meta_tags:
                for tag in process.config.meta_tags:
                    tags.add(tag.lower())
            return search_text.lower() in process.name or search_text.lower() in tags

        def filter_(search_text: str, process: Process) -> bool:
            if search_text.startswith(prefix):
                return filter_against_category(search_text, process)
            return filter_against_name_and_meta(search_text, process)

        self.filtered_process_list = self._sort_process_list([p for p in self.process_list if filter_(self._filter, p)])
        self.selected_process = self.filtered_process_list[0] if self.filtered_process_list else None

    def register_focusable_element(self, target: FocusTarget):
        self.focus_targets.append(target)

    def deregister_focusable_element(self, widget: FocusWidget):
        self.focus_targets = [fe for fe in self.focus_targets if fe.widget != widget]

    def get_focus_element(self, widget: FocusWidget) -> Optional[Any]:
        for target in self.focus_targets:
            if target.widget == widget:
                return target.element
        return None

    def start_interpolating(self, command_form: Any):
        self._command_form = command_form
        self.interpolating = True

    def stop_interpolating(self):
        self.interpolating = False
        self._command_form = None
