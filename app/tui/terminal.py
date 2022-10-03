from prompt_toolkit.layout import DynamicContainer, VSplit  # , Window
from prompt_toolkit.widgets import Frame

from app.tui.controller import ProcMuxController
from app.tui.keybindings import DocumentedKeybindings, register_app_wide_configured_keybindings
from app.tui.state import FocusWidget


class TerminalPanel:
    def __init__(self, controller: ProcMuxController):
        self._controller: ProcMuxController = controller
        self._container: Frame = Frame(
            title='Terminal',
            body=VSplit([
                DynamicContainer(get_container=lambda: self._controller.current_terminal),
            ]))
        self._controller.register_focusable_element(FocusWidget.TERMINAL,
                                                    element=self,
                                                    keybinding_help=self.get_keybindings().help_docs)

    def get_keybindings(self) -> DocumentedKeybindings:
        return register_app_wide_configured_keybindings(self._controller.config,
                                                        self._controller.switch_focus,
                                                        self._controller.zoom,
                                                        self._controller.toggle_scroll,
                                                        DocumentedKeybindings())

    def __pt_container__(self):
        return self._container
