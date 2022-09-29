from typing import Callable

from prompt_toolkit.layout import DynamicContainer, UIControl
from prompt_toolkit.widgets import Frame

from app.context import ProcMuxContext
from app.tui.focus import FocusManager


class TerminalPanel:
    def __init__(
            self,
            get_current_terminal: Callable,
            focus_manager: FocusManager,
    ):
        self._focus_manager = focus_manager
        self._ctx = ProcMuxContext()
        self._container = Frame(title='Terminal',
                                body=UIControl(DynamicContainer(get_container=get_current_terminal)))
