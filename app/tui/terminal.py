from prompt_toolkit.key_binding import KeyBindings

from prompt_toolkit.layout import DynamicContainer, VSplit  # , Window
from prompt_toolkit.widgets import Frame

from app.tui.controller import ProcMuxController
from app.tui.keybindings import register_app_wide_configured_keybindings


class TerminalPanel:
    def __init__(self, controller: ProcMuxController):
        self._controller: ProcMuxController = controller
        self._container: Frame = Frame(
            title='Terminal',
            body=VSplit([
                DynamicContainer(get_container=lambda: self._controller.current_terminal),
            ]))

    def get_keybindings(self):
        return register_app_wide_configured_keybindings(self._controller.config,
                                                        self._controller.switch_focus,
                                                        self._controller.zoom,
                                                        self._controller.toggle_scroll,
                                                        KeyBindings())

    def __pt_container__(self):
        return self._container
