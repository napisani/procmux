from __future__ import unicode_literals

from typing import Callable, List

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import ConditionalContainer, DynamicContainer, HSplit, Layout, VSplit, Window
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.widgets import Frame
from ptterm import Terminal

from app.context import ProcMuxContext
from app.exec import TerminalManager
from app.log import logger
from app.tui.focus import FocusManager
from app.tui.help import HelpPanel
from app.tui.process_description import ProcessDescriptionPanel
from app.tui.side_bar import SideBar

_width_100 = _height_100 = D(preferred=100 * 100)


def _create_terminal(cmd: List[str], before_exec: Callable, on_done: Callable) -> Terminal:
    return Terminal(
        command=cmd,
        width=_width_100,
        height=_height_100,
        style='class:terminal',
        done_callback=on_done,
        before_exec_func=before_exec)


def _prep_tui_state():
    ctx = ProcMuxContext()
    if ctx.config.layout.sort_process_list_alpha:
        ctx.tui_state.process_name_list = sorted(ctx.config.procs.keys())
    else:
        ctx.tui_state.process_name_list = ctx.config.procs.keys()
    ctx.tui_state.selected_process_name = None
    if ctx.config.procs:
        ctx.tui_state.selected_process_idx = 0
    terminal_managers = [
        TerminalManager(proc_name, _create_terminal)
        for proc_name in ctx.tui_state.process_name_list
    ]
    ctx.tui_state.terminal_managers = terminal_managers


def start_tui():
    _prep_tui_state()

    ctx = ProcMuxContext()

    def _handle_cmd_started(proc_idx: int):
        nonlocal current_terminal
        current_terminal = ctx.tui_state.terminal_managers[proc_idx].spawn_terminal()

    def _handle_process_focus_changed(proc_idx: int):
        nonlocal current_terminal
        nonlocal terminal_placeholder
        term = ctx.tui_state.terminal_managers[proc_idx].get_terminal()
        if not term:
            term = terminal_placeholder
        current_terminal = term

    def _handle_stop_cmd(proc_idx: int):
        nonlocal current_terminal
        ctx.tui_state.terminal_managers[proc_idx].send_kill_signal()

    def _handle_quit():
        application.exit()

    terminal_placeholder = Window(style=f'bg:{ctx.config.style.placeholder_terminal_bg_color}',
                                  width=_width_100,
                                  height=_height_100)
    current_terminal = terminal_placeholder

    def _on_terminal_change(term):
        nonlocal current_terminal
        current_terminal = term

    focus_manager = FocusManager(on_terminal_change=_on_terminal_change)

    side_bar = SideBar(
        focus_manager=focus_manager,
        on_start=_handle_cmd_started,
        on_stop=_handle_stop_cmd,
        on_down=_handle_process_focus_changed,
        on_up=_handle_process_focus_changed,
        on_quit=_handle_quit)

    def _get_current_terminal():
        return current_terminal

    terminal_wrapper = Frame(title='Terminal',
                             body=DynamicContainer(get_container=_get_current_terminal))
    kb = KeyBindings()

    for keybinding in ctx.config.keybinding.switch_focus:
        @kb.add(keybinding)
        def _switch_focus(_event):
            logger.info('in _switch_focus')
            focus_manager.toggle_sidebar_terminal_focus()

    for keybinding in ctx.config.keybinding.zoom:
        @kb.add(keybinding)
        def _zoom(_event):
            logger.info('in _zoom')
            focus_manager.toggle_zoom()

    main_layout_container = HSplit([
        VSplit([
            side_bar,
            terminal_wrapper

        ]),
        ConditionalContainer(content=ProcessDescriptionPanel(),
                             filter=not ctx.config.layout.hide_process_description_panel),
        ConditionalContainer(content=HelpPanel(focus_manager=focus_manager),
                             filter=not ctx.config.layout.hide_help)
    ])

    def _get_layout_container():
        if ctx.tui_state.zoomed_in:
            return _get_current_terminal()
        return main_layout_container

    application = Application(
        layout=Layout(
            container=DynamicContainer(get_container=_get_layout_container),
            focused_element=side_bar),
        key_bindings=kb,
        full_screen=True,
        mouse_support=False,
    )

    def refresh_app():
        nonlocal application
        application.invalidate()

    for manager in ctx.tui_state.terminal_managers:
        manager.register_process_done_handler(refresh_app)
        manager.register_process_spawn_handler(refresh_app)
        manager.autostart_conditionally()
        refresh_app()

    application.run()
