from __future__ import unicode_literals

from typing import Callable, List

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import DynamicKeyBindings, KeyBindings
from prompt_toolkit.layout import ConditionalContainer, DynamicContainer, HSplit, Layout, VSplit
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.styles import Style
from ptterm import Terminal

from app.context import ProcMuxContext
from app.exec import TerminalManager
from app.tui.docs import DocsDialog
from app.tui.focus import FocusManager
from app.tui.help import HelpPanel
from app.tui.process_description import ProcessDescriptionPanel
from app.tui.side_bar import SideBar
from app.tui.style import height_100, width_100
from app.tui.terminal import TerminalPanel
from app.tui_state import FocusWidget


def _create_terminal(cmd: List[str],
                     before_exec: Callable,
                     on_done: Callable) -> Terminal:
    return Terminal(
        command=cmd,
        width=width_100,
        height=height_100,
        style='class:terminal',
        done_callback=on_done,
        before_exec_func=before_exec)


def _prep_tui_state():
    ctx = ProcMuxContext()
    if ctx.config.layout.sort_process_list_alpha:
        ctx.tui_state.process_name_list = sorted(list(ctx.config.procs.keys()))
    else:
        ctx.tui_state.process_name_list = list(ctx.config.procs.keys())
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

    def _on_terminal_change(term):
        terminal_wrapper.set_current_terminal(term)

    focus_manager = FocusManager(on_terminal_change=_on_terminal_change)
    terminal_wrapper = TerminalPanel(focus_manager=focus_manager)

    def _on_sidebar_mouse_event(mouse_event: MouseEvent):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            _, y = mouse_event.position
            ctx.tui_state.selected_process_idx = y
            terminal_wrapper.set_terminal_terminal_by_process_idx(y)
            focus_manager.focus_to_sidebar()

    side_bar = SideBar(
        focus_manager=focus_manager,
        on_start=lambda proc_idx: terminal_wrapper.start_cmd_in_terminal(proc_idx),
        on_stop=lambda proc_idx: terminal_wrapper.stop_command(proc_idx),
        on_down=lambda proc_idx: terminal_wrapper.set_terminal_terminal_by_process_idx(proc_idx),
        on_up=lambda proc_idx: terminal_wrapper.set_terminal_terminal_by_process_idx(proc_idx),
        on_mouse_event=_on_sidebar_mouse_event
    )

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
    docs_layout_container = HSplit([
        DocsDialog(focus_manager),
        ConditionalContainer(content=ProcessDescriptionPanel(),
                             filter=not ctx.config.layout.hide_process_description_panel),
        ConditionalContainer(content=HelpPanel(focus_manager=focus_manager),
                             filter=not ctx.config.layout.hide_help)
    ])

    def _get_layout_container():
        if ctx.tui_state.zoomed_in:
            return terminal_wrapper.get_current_terminal()
        elif ctx.tui_state.docs_open:
            return docs_layout_container
        return main_layout_container

    def _get_app_keybindings():
        if focus_manager.get_focused_widget() == FocusWidget.TERMINAL:
            return terminal_wrapper.get_keybindings()
        return KeyBindings()

    application = Application(
        layout=Layout(
            container=DynamicContainer(get_container=_get_layout_container),
            focused_element=side_bar),
        full_screen=True,
        mouse_support=ctx.config.enable_mouse,
        key_bindings=DynamicKeyBindings(get_key_bindings=_get_app_keybindings),
        style=Style(list((ctx.config.style.style_classes or {}).items())),
        color_depth=ctx.config.style.color_depth
    )

    def refresh_app():
        application.invalidate()

    for manager in ctx.tui_state.terminal_managers:
        manager.register_process_done_handler(refresh_app)
        manager.register_process_spawn_handler(refresh_app)
        manager.autostart_conditionally()
        refresh_app()

    application.run()
