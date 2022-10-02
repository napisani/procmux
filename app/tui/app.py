from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import DynamicKeyBindings, KeyBindings
from prompt_toolkit.layout import ConditionalContainer, DynamicContainer, HSplit, Layout, VSplit
from prompt_toolkit.styles import Style

from app.config import ProcMuxConfig
from app.tui.command_form import CommandForm
from app.tui.controller import ProcMuxController
from app.tui.docs import DocsDialog
from app.tui.help import HelpPanel
from app.tui.process_description import ProcessDescriptionPanel
from app.tui.side_bar import SideBar
from app.tui.state import FocusWidget, TUIState
from app.tui.terminal import TerminalPanel


def start_tui(config: ProcMuxConfig):
    controller = ProcMuxController(TUIState(config), CommandForm)

    terminal_wrapper = TerminalPanel(controller)
    side_bar = SideBar(controller)

    main_layout_container = HSplit([
        VSplit([
            side_bar,
            terminal_wrapper
        ]),
        ConditionalContainer(content=ProcessDescriptionPanel(controller),
                             filter=not controller.config.layout.hide_process_description_panel),
        ConditionalContainer(content=HelpPanel(controller),
                             filter=not controller.config.layout.hide_help)
    ])

    docs_layout_container = HSplit([
        DocsDialog(controller),
        ConditionalContainer(content=ProcessDescriptionPanel(controller),
                             filter=not controller.config.layout.hide_process_description_panel),
        ConditionalContainer(content=HelpPanel(controller),
                             filter=not controller.config.layout.hide_help)
    ])

    def _get_layout_container():
        if controller.zoomed_in:
            return controller.current_terminal
        elif controller.docs_open:
            return docs_layout_container
        return main_layout_container

    def _get_app_keybindings():
        if controller.focused_widget == FocusWidget.TERMINAL:
            return terminal_wrapper.get_keybindings()
        return KeyBindings()

    application = Application(
        layout=Layout(
            container=DynamicContainer(get_container=_get_layout_container),
            focused_element=side_bar),
        full_screen=True,
        mouse_support=controller.config.enable_mouse,
        key_bindings=DynamicKeyBindings(get_key_bindings=_get_app_keybindings),
        style=Style(list((controller.config.style.style_classes or {}).items())),
        color_depth=controller.config.style.color_depth
    )

    controller.autostart()
    application.run()
