from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import DynamicKeyBindings
from prompt_toolkit.layout import ConditionalContainer, DynamicContainer, FloatContainer, HSplit, Layout, VSplit, Window
from prompt_toolkit.styles import Style

from procmux.config import ProcMuxConfig
from procmux.tui.controller.tui_controller import TUIController
from procmux.tui.view.docs import DocsDialog
from procmux.tui.view.help import HelpPanel
from procmux.tui.view.process_description import ProcessDescriptionPanel
from procmux.tui.view.side_bar import SideBar
from procmux.tui.view.terminal import TerminalPanel


def start_tui(config: ProcMuxConfig):
    terminal_placeholder = Window(
        style=f'bg:{config.style.placeholder_terminal_bg_color}',
        width=config.style.width_100,
        height=config.style.height_100)

    dynamic_container = DynamicContainer(get_container=lambda: None)
    float_container = FloatContainer(content=dynamic_container, floats=[])

    controller = TUIController(config, terminal_placeholder, float_container)

    side_bar = SideBar(controller)

    main_layout_container = HSplit([
        VSplit([side_bar, TerminalPanel(controller)]),
        ConditionalContainer(
            content=ProcessDescriptionPanel(controller),
            filter=not controller.config.layout.hide_process_description_panel
        ),
        ConditionalContainer(content=HelpPanel(controller),
                             filter=not controller.config.layout.hide_help)
    ])

    docs_layout_container = HSplit([
        DocsDialog(controller),
        ConditionalContainer(
            content=ProcessDescriptionPanel(controller),
            filter=not controller.config.layout.hide_process_description_panel
        ),
        ConditionalContainer(content=HelpPanel(controller),
                             filter=not controller.config.layout.hide_help)
    ])

    def _get_layout_container():
        if controller.zoomed_in:
            return controller.current_terminal
        elif controller.docs_open:
            return docs_layout_container
        return main_layout_container

    dynamic_container.get_container = _get_layout_container

    application = Application(
        layout=Layout(container=controller.float_container,
                      focused_element=side_bar),
        full_screen=True,
        mouse_support=controller.config.enable_mouse,
        key_bindings=DynamicKeyBindings(
            get_key_bindings=controller.get_app_keybindings),
        style=Style(list((controller.config.style.style_classes
                          or {}).items())),
        color_depth=controller.config.style.color_depth)

    controller.autostart()
    application.run()
