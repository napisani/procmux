from typing import List

from prompt_toolkit.layout import DynamicContainer, HSplit, VSplit, Window
from prompt_toolkit.widgets import Frame, TextArea

from app.context import ProcMuxContext
from app.interpolation import Interpolation
from app.tui.focus import FocusManager
from app.tui.keybindings import register_app_wide_configured_keybindings
from app.tui.style import height_100, width_100
from app.tui_state import FocusWidget


class TerminalPanel:
    def __init__(
            self,
            focus_manager: FocusManager,
    ):
        self._focus_manager = focus_manager
        self._ctx = ProcMuxContext()
        self._terminal_placeholder = Window(
            style=f'bg:{self._ctx.config.style.placeholder_terminal_bg_color}',
            width=width_100,
            height=height_100)
        self._current_terminal = self._terminal_placeholder
        self._container = Frame(
            title='Terminal',
            body=VSplit([
                DynamicContainer(get_container=lambda: self._current_terminal),
            ]))

    def start_cmd_in_terminal(self, proc_idx: int):
        if self._ctx.tui_state.quitting:
            return  # if procmux is in the process of quitting, don't start a new process
        proc_name = self._ctx.tui_state.process_name_list[proc_idx]
        proc = self._ctx.config.procs[proc_name]
        interpolations = proc.interpolations
        if len(interpolations) > 0:
            form = self._build_input_form(interpolations)
            self._focus_manager.register_focusable_element(FocusWidget.TERMINAL_COMMAND_INPUTS, form)
            self.set_current_terminal(form)
            self._focus_manager.set_focus(form)
            return

        terminal_manger = self._ctx.tui_state.terminal_managers[proc_idx]
        self._current_terminal = terminal_manger.spawn_terminal()

    def _build_input_form(self, interpolations: List[Interpolation]):
        return HSplit([
            TextArea(
                height=1,
                prompt=f"{interp.field} >>> ",
                style="class:input-field",
                multiline=False,
                wrap_lines=False,
            ) for interp in interpolations
        ])

    def stop_command(self, proc_idx: int):
        self._ctx.tui_state.terminal_managers[proc_idx].send_kill_signal()

    def set_current_terminal(self, term):
        self._current_terminal = term

    def get_current_terminal(self):
        self._current_terminal

    def set_terminal_terminal_by_process_idx(self, proc_idx: int):
        term = self._ctx.tui_state.terminal_managers[proc_idx].get_terminal()
        if not term:
            term = self._terminal_placeholder
        self._current_terminal = term

    def get_keybindings(self):
        kb = register_app_wide_configured_keybindings(self._focus_manager)
        return kb

    def __pt_container__(self):
        return self._container
