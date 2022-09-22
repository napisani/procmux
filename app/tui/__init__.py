from __future__ import unicode_literals

from typing import Callable, List

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import ConditionalContainer, DynamicContainer, HSplit, Layout, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame
from ptterm import Terminal

from app.context import ProcMuxContext
from app.exec import TerminalManager
from app.log import logger
from app.tui.help import HelpPanel
from app.tui.side_bar import SideBar
from app.tui_state import FocusWidget

logger.info('run')


def _create_terminal(cmd: List[str], on_done: Callable) -> Terminal:
    return Terminal(
        command=cmd,
        width=D(preferred=80),
        height=D(preferred=40),
        style='class:terminal',
        done_callback=on_done)


def _prep_tui_state():
    ctx = ProcMuxContext()
    ctx.tui_state.process_name_list = sorted(ctx.proc_managers.keys())
    ctx.tui_state.selected_process_name = None
    if ctx.proc_managers:
        ctx.tui_state.selected_process_idx = 0
    terminal_managers = [
        TerminalManager(proc_name, _create_terminal)
        for proc_name in ctx.tui_state.process_name_list
    ]
    ctx.tui_state.terminal_managers = terminal_managers
    ctx.tui_state.focus = FocusWidget.SIDE_BAR


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

    side_bar = SideBar(on_start=_handle_cmd_started,
                       on_stop=_handle_stop_cmd,
                       on_down=_handle_process_focus_changed,
                       on_up=_handle_process_focus_changed,
                       on_quit=_handle_quit)
    terminal_placeholder = Window(style=f'bg:{ctx.config.style.placeholder_terminal_bg_color}',
                                  width=D(preferred=100 * 100),  # max width of parent
                                  height=D(preferred=100 * 100))
    current_terminal = terminal_placeholder

    def _get_current_terminal():
        return current_terminal

    terminal_wrapper = Frame(title='Terminal',
                             body=DynamicContainer(get_container=_get_current_terminal))
    kb = KeyBindings()

    for keybinding in ctx.config.keybinding.switch_focus:
        @kb.add(keybinding)
        def _switch_focus(_event):
            logger.info('in _switch_focus')
            switch_focus()

    def switch_focus():
        idx = ctx.tui_state.selected_process_idx
        if not application.layout.has_focus(side_bar):
            logger.info('focusing on sidebar')
            application.layout.focus(side_bar)
            ctx.tui_state.focus = FocusWidget.SIDE_BAR
        elif idx is not None:
            t_manager = ctx.tui_state.terminal_managers[idx]
            term = t_manager.get_terminal()
            if term:
                nonlocal current_terminal
                current_terminal = term
                application.layout.focus(term)
                ctx.tui_state.focus = FocusWidget.TERMINAL
                logger.info(f'focusing on terminal for idx: {idx} ')

    application = Application(
        layout=Layout(
            container=HSplit([
                VSplit([
                    side_bar,
                    terminal_wrapper

                ]),
                ConditionalContainer(content=HelpPanel(),
                                     filter=not ctx.config.layout.hide_help)
            ]),
            focused_element=side_bar
        ),
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
    application.run()
