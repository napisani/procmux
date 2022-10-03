from copy import deepcopy
from functools import cached_property
from typing import Any, Callable, List, Optional, Union

from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Window
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from ptterm import Terminal

from app.config import ProcMuxConfig
from app.interpolation import Interpolation
from app.log import logger
from app.terminal_manager import TerminalManager
from app.tui.state import FocusTarget, FocusWidget, KeybindingDocumentation, Process, TUIState

"""
ProxMuxController is responsible for updating state and sharing
state changes with registered handlers
"""


class ProcMuxController:
    def __init__(self, tui_state: TUIState, command_form_ctor):
        self._tui_state: TUIState = tui_state
        self._command_form_ctor = command_form_ctor
        self._on_scroll_mode_changed_handlers: List[Callable[[int, bool], None]] = []
        for tm in self._tui_state.terminal_managers.values():
            tm.register_on_process_spawned_handler(self.on_process_spawned)
            tm.register_on_process_done_handler(self.on_process_done)
            self.register_scroll_mode_change_handler(tm.on_scroll_mode_change)

    @cached_property
    def config(self) -> ProcMuxConfig:
        return deepcopy(self._tui_state.config)

    @property
    def zoomed_in(self) -> bool:
        return self._tui_state.zoomed_in

    @property
    def filter_mode(self) -> bool:
        return self._tui_state.filter_mode

    @property
    def docs_open(self) -> bool:
        return self._tui_state.docs_open

    @property
    def quitting(self) -> bool:
        return self._tui_state.quitting

    @property
    def interpolating(self) -> bool:
        return self._tui_state.interpolating

    # Processes

    @property
    def process_list(self) -> List[Process]:
        return self._tui_state.process_list

    @property
    def filtered_process_list(self) -> List[Process]:
        return self._tui_state.filtered_process_list

    @property
    def selected_process(self) -> Optional[Process]:
        return self._tui_state.selected_process

    @property
    def is_selected_process_running(self) -> bool:
        return self.selected_process.running if self.selected_process else False

    @property
    def selected_process_has_terminal(self) -> bool:
        return self.current_terminal_manager is not None \
               and self.current_terminal_manager.terminal is not None

    def is_selected_process(self, process: Process) -> bool:
        if self.selected_process:
            return self.selected_process.index == process.index
        return False

    def start_process(self, process: Optional[Process] = None):
        logger.info(f'in start_process {process.name if process else ""}')
        if process:
            self.start_process_in_terminal(process)
            return
        if self.selected_process:
            self.start_process_in_terminal(self.selected_process)

    def stop_process(self):
        logger.info('in stop_process')
        if self.current_terminal_manager:
            self.current_terminal_manager.send_kill_signal()

    def on_process_spawned(self, index: int):
        logger.info('in on process spawned')
        for process in self.process_list:
            if process.index == index:
                logger.info(f'process {process.name} spawned')
                process.running = True

    def on_process_done(self, index: int):
        logger.info('in on process done')
        for process in self.process_list:
            if process.index == index:
                logger.info(f'process {process.name} done')
                process.running = False
                if self.quitting and not self._tui_state.has_running_processes:
                    self._quit()
                self.refresh_app()

    # /Processes

    # Terminal

    @property
    def current_terminal(self) -> Union[Terminal, Window, Any]:
        return self._tui_state.current_terminal

    @property
    def current_terminal_manager(self) -> Optional[TerminalManager]:
        return self._tui_state.current_terminal_manager

    def start_process_in_terminal(self, process: Process):
        logger.info(f'starting {process.name} in terminal')
        if self.quitting:
            return  # if procmux is in the process of quitting, don't start a new process

        def finish_interpolating():
            self._tui_state.stop_interpolating()
            self.deregister_focusable_element(FocusWidget.TERMINAL_COMMAND_INPUTS)
            self.focus_to_sidebar()

        def start_cmd(final_interpolations: Optional[List[Interpolation]] = None):
            if self.interpolating:
                finish_interpolating()
            terminal_manager = self._tui_state.terminal_managers[process.index]
            if terminal_manager:
                run_in_background = self.selected_process is None or self.selected_process.index != process.index
                terminal_manager.spawn_terminal(run_in_background, final_interpolations)

        if len(process.config.interpolations) > 0:
            form = self._command_form_ctor(self,
                                           process.config.interpolations,
                                           start_cmd,
                                           finish_interpolating)
            kb = form.get_keybindings()
            self.register_focusable_element(FocusWidget.TERMINAL_COMMAND_INPUTS, form, kb.help_docs)
            self._tui_state.start_interpolating(form)
            self.focused_widget = FocusWidget.TERMINAL_COMMAND_INPUTS
            return
        start_cmd()

    # /Terminal

    # Focus
    def _focused_target(self) -> Optional[FocusTarget]:
        app = get_app()
        if app:
            for target in self._tui_state.focus_targets:
                if app.layout.has_focus(target.element):
                    return target
        return None

    @property
    def focused_widget(self) -> FocusWidget:
        target = self._focused_target()
        if not target:
            return FocusWidget.TERMINAL
        return target.widget

    @focused_widget.setter
    def focused_widget(self, value: FocusWidget):
        self._set_focus(self._tui_state.get_focus_element(value))

    @property
    def focused_keybinding_help(self) -> List[KeybindingDocumentation]:
        target = self._focused_target()
        if not target or not target.keybinding_help:
            return []
        return target.keybinding_help

    @property
    def is_focused_on_free_form_input(self):
        return self.focused_widget == FocusWidget.SIDE_BAR_FILTER

    def _set_focus(self, element: Optional[Any]):
        app = get_app()
        if app and element:
            app.layout.focus(element)

    def register_focusable_element(
            self,
            widget: FocusWidget,
            element: Any,
            keybinding_help: List[KeybindingDocumentation] = None):
        if keybinding_help is None:
            keybinding_help = []

        self._tui_state.register_focusable_element(
            FocusTarget(widget=widget,
                        element=element,
                        keybinding_help=keybinding_help))

    def deregister_focusable_element(self, widget: FocusWidget):
        self._tui_state.deregister_focusable_element(widget)

    def focus_to_current_terminal(self) -> bool:
        logger.info('focusing on current terminal')
        if self.current_terminal:
            application = get_app()
            if application:
                application.layout.focus(self.current_terminal)
                logger.info('focusing on selected process terminal')
            return True
        return False

    def toggle_sidebar_terminal_focus(self):
        logger.info(f'toggling focus between sidebar and terminal- focus_widget:{self.focused_widget}')
        if self.docs_open:
            logger.info('in toggle_sidebar_terminal_focus - but the docs are open, toggling docs off instead')
            self.toggle_docs()
            return
        if self.zoomed_in:
            logger.info('in toggle_sidebar_terminal_focus - currently zoomed in, toggling zoom off instead')
            self.toggle_zoom()
            return
        if self.focused_widget == FocusWidget.TERMINAL:
            logger.info('currently focused on terminal switching to sidebar')
            self.focus_to_sidebar()
        elif self.focused_widget == FocusWidget.SIDE_BAR_SELECT:
            logger.info('currently focused on sidebar switching to terminal')
            self.focus_to_current_terminal()

    def focus_to_sidebar(self):
        logger.info('focusing on sidebar')
        self.focused_widget = FocusWidget.SIDE_BAR_SELECT

    # /Focus

    # Sidebar

    def on_sidebar_mouse_event(self, event: MouseEvent):
        logger.info(f'in sidebar mouse event: {event}')
        if event.event_type == MouseEventType.MOUSE_UP:
            _, y = event.position
            self._tui_state.set_selected_process_by_index(y)
            self.focus_to_sidebar()

    def move_process_selection(self, direction: int):
        if not self.selected_process:
            self._tui_state.select_first_process()
            return

        if len(self.filtered_process_list) < 2:
            self._tui_state.select_first_process()
            return

        available_indices = [p.index for p in self.filtered_process_list]

        if self.selected_process.index not in available_indices:
            self._tui_state.select_first_process()
            return

        current_index = available_indices.index(self.selected_process.index)
        new_index = ((current_index + direction) % len(self.filtered_process_list))
        self._tui_state.set_selected_process_by_index(new_index)

    def sidebar_up(self):
        self.move_process_selection(-1)

    def sidebar_down(self):
        self.move_process_selection(1)

    def start_filter(self):
        logger.info('in start_filter')
        self._tui_state.filter_mode = True
        self._tui_state.selected_process = None
        self.focused_widget = FocusWidget.SIDE_BAR_FILTER

    def update_filter(self, buffer: Buffer):
        logger.info(f'in update filter: {buffer.text}')
        self._tui_state.apply_filter(buffer.text)

    def exit_filter(self, search_text: str):
        logger.info(f'in exit_filter: {search_text}')
        self._tui_state.apply_filter(search_text)
        self._tui_state.filter_mode = False
        self.focus_to_sidebar()

    def view_docs(self):
        logger.info('in view_docs')
        self.toggle_docs()

    def close_docs(self):
        logger.info('in close_docs')
        self.toggle_docs()

    def toggle_docs(self):
        logger.info(f'setting docks_open to {not self.docs_open}')
        self._tui_state.docs_open = not self.docs_open
        if self.docs_open:
            self.focused_widget = FocusWidget.DOCS
        else:
            self.focused_widget = FocusWidget.SIDE_BAR_SELECT

    def switch_focus(self):
        logger.info('in switch_focus')
        if not self.is_focused_on_free_form_input:
            self.toggle_sidebar_terminal_focus()

    def zoom(self):
        logger.info('in zoom')
        if not self.is_focused_on_free_form_input:
            self.toggle_zoom()

    def toggle_zoom(self):
        logger.info('in toggle_zoom')
        if self.zoomed_in:
            logger.info('setting zoomed_in to False')
            self._tui_state.zoomed_in = False
            self.focus_to_sidebar()
        else:
            if self.focus_to_current_terminal():
                logger.info('setting zoomed_in to True')
                self._tui_state.zoomed_in = True

    # /Sidebar

    # Scroll

    def register_scroll_mode_change_handler(self, handler: Callable[[int, bool], None]):
        self._on_scroll_mode_changed_handlers.append(handler)

    def on_scroll_mode_change(self, process: Process):
        for handler in self._on_scroll_mode_changed_handlers:
            handler(process.index, process.scroll_mode)

    def toggle_scroll(self):
        logger.info('in _toggle_scroll')
        if not self.is_focused_on_free_form_input and self.selected_process:
            self.selected_process.scroll_mode = not self.selected_process.scroll_mode
            self.on_scroll_mode_change(self.selected_process)
            if not self.selected_process.scroll_mode and not self.zoomed_in:
                self.focus_to_sidebar()

    # /Scroll

    def autostart(self):
        logger.info('in autostart')
        for process in self.process_list:
            if process.config.autostart:
                logger.info(f'autostarting {process.name}')
                assert not process.config.interpolations, \
                    'processes with autostart enabled must not have interpolations/field replacements'
                self.start_process(process)

    def quit(self):
        logger.info('in quit')
        application = get_app()

        if not application or self.quitting:
            return  # avoid registering process done handler multiple times
        self._tui_state.quitting = True
        logger.info('quit - sending kill signals')
        for tm in self._tui_state.terminal_managers.values():
            tm.send_kill_signal()
        if not self._tui_state.has_running_processes:
            application.exit()

    def _quit(self):
        application = get_app()
        if application:
            application.exit()

    def refresh_app(self):
        app = get_app()
        if app:
            app.invalidate()
