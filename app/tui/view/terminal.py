from prompt_toolkit.layout import Dimension, DynamicContainer, VSplit
from prompt_toolkit.widgets import Box, Frame

from app.tui.controller.tui_controller import TUIController
from app.tui.types import FocusWidget


class TerminalPanel:

    def __init__(self, controller: TUIController):
        self._controller: TUIController = controller
        width = Dimension(min=0, max=100000, weight=1)
        height = Dimension(min=0, max=100000, weight=1)

        body = VSplit([
            DynamicContainer(
                get_container=lambda: self._controller.current_terminal),
        ])
        if self._controller.config.style.show_borders:
            self._container = Frame(title='Terminal',
                                    width=width,
                                    height=height,
                                    body=body)
        else:
            self._container = Box(
                body=body,
                width=width,
                height=height,
            )
        self._controller.register_focusable_element(FocusWidget.TERMINAL,
                                                    element=self)

    def __pt_container__(self):
        return self._container
