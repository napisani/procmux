from copy import deepcopy
from functools import cached_property
from typing import Any, Dict, List, Optional, Union

from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Window
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from ptterm import Terminal

from app.config import ProcMuxConfig
from app.log import logger
from app.tui.controller.terminal_controller import TerminalController
from app.tui.state.process_state import ProcessState
from app.tui.state.tui_state import TUIState
from app.tui.types import FocusTarget, FocusWidget, KeybindingDocumentation, Process
from app.util.interpolation import Interpolation


class TUIController:
    def __init__(self, config: ProcMuxConfig, terminal_placeholder: Window, command_form_ctor):
        self._terminal_placeholder = terminal_placeholder
        self._command_form_ctor = command_form_ctor
        self._tui_state: TUIState = TUIState(config)
        self._process_state: ProcessState = ProcessState(config)
        self._terminal_controllers: Dict[int, TerminalController] = \
            self._create_terminal_controllers(config, self._process_state.process_list)

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
        return self._process_state.process_list

    @property
    def filtered_process_list(self) -> List[Process]:
        return self._process_state.filtered_process_list

    @property
    def selected_process(self) -> Optional[Process]:
        return self._process_state.selected_process

    @property
    def is_selected_process_running(self) -> bool:
        return self._process_state.is_selected_process_running

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
        if self.current_terminal_controller:
            self.current_terminal_controller.stop_process()

    def on_process_spawned(self, process: Process):
        logger.info(f'in on process spawned: {process.name}')
        process.running = True

    def on_process_done(self, process: Process):
        logger.info(f'in on process done: {process.name}')
        process.running = False
        if self.quitting and not self._process_state.has_running_processes:
            self._quit()
        self.refresh_app()

    # /Processes

    # Terminal

    @property
    def current_terminal_controller(self) -> Optional[TerminalController]:
        if self.selected_process:
            return self._terminal_controllers.get(self.selected_process.index, None)
        return None

    @property
    def current_terminal(self) -> Union[Terminal, Window, Any]:
        if self.interpolating and self._tui_state._command_form:
            return self._tui_state._command_form
        if self.current_terminal_controller and self.current_terminal_controller.terminal:
            return self.current_terminal_controller.terminal
        return self._terminal_placeholder

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
            terminal_controller = self._terminal_controllers[process.index]
            if terminal_controller:
                run_in_background = self.selected_process is None or self.selected_process.index != process.index
                terminal_controller.spawn_terminal(run_in_background, final_interpolations)

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
            keybinding_help: Optional[List[KeybindingDocumentation]] = None):
        self._tui_state.register_focusable_element(
            FocusTarget(widget=widget,
                        element=element,
                        keybinding_help=keybinding_help if keybinding_help else []))

    def deregister_focusable_element(self, widget: FocusWidget):
        self._tui_state.deregister_focusable_element(widget)

    def focus_to_current_terminal(self) -> bool:
        logger.info('focusing on current terminal')
        if self.current_terminal:
            application = get_app()
            if application:
                logger.info('focusing on selected process terminal')
                application.layout.focus(self.current_terminal)
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
            self._process_state.set_selected_process_by_y_pos(y)
            self.focus_to_sidebar()

    def move_process_selection(self, direction: int):
        if not self.selected_process:
            self._process_state.select_first_process()
            return

        if len(self.filtered_process_list) < 2:
            self._process_state.select_first_process()
            return

        available_indices = [p.index for p in self.filtered_process_list]

        if self.selected_process.index not in available_indices:
            self._process_state.select_first_process()
            return

        current_index = available_indices.index(self.selected_process.index)
        new_index = ((current_index + direction) % len(self.filtered_process_list))
        self._process_state.set_selected_process_by_y_pos(new_index)

    def sidebar_up(self):
        self.move_process_selection(-1)

    def sidebar_down(self):
        self.move_process_selection(1)

    def start_filter(self):
        logger.info('in start_filter')
        self._tui_state.filter_mode = True
        self._process_state.selected_process = None
        self.focused_widget = FocusWidget.SIDE_BAR_FILTER

    def update_filter(self, buffer: Buffer):
        logger.info(f'in update filter: {buffer.text}')
        self._process_state.apply_filter(buffer.text)

    def exit_filter(self, search_text: str):
        logger.info(f'in exit_filter: {search_text}')
        self._process_state.apply_filter(search_text)
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

    def on_scroll_mode_change(self, process: Process):
        terminal_controller = self._terminal_controllers[process.index]
        if terminal_controller:
            terminal_controller.on_scroll_mode_change(process.scroll_mode)

    def toggle_scroll(self):
        logger.info('in _toggle_scroll')
        if not self.is_focused_on_free_form_input and self.selected_process:
            self.selected_process.scroll_mode = not self.selected_process.scroll_mode
            self.on_scroll_mode_change(self.selected_process)
            if not self.selected_process.scroll_mode and not self.zoomed_in:
                self.focus_to_sidebar()

    # /Scroll

    def _create_terminal_controllers(self,
                                     config: ProcMuxConfig,
                                     process_list: List[Process],
                                     ) -> Dict[int, TerminalController]:
        return {p.index: TerminalController(self, config, p) for p in process_list}

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
        for tc in self._terminal_controllers.values():
            tc.stop_process()
        if not self._process_state.has_running_processes:
            application.exit()

    def _quit(self):
        application = get_app()
        if application:
            application.exit()

    def refresh_app(self):
        app = get_app()
        if app:
            app.invalidate()
