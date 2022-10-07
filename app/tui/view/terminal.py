from prompt_toolkit.layout import DynamicContainer, VSplit  # , Window
from prompt_toolkit.widgets import Frame

from app.tui.types import FocusWidget
from app.tui.controller.tui_controller import TUIController


class TerminalPanel:
    def __init__(self, controller: TUIController):
        self._controller: TUIController = controller
        self._container: Frame = Frame(
            title='Terminal',
            body=VSplit([
                DynamicContainer(get_container=lambda: self._controller.current_terminal),
            ]))
        self._controller.register_focusable_element(FocusWidget.TERMINAL, element=self)

    def __pt_container__(self):
        return self._container
