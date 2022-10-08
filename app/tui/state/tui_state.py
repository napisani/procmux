from typing import Any, List, Optional

from app.config import ProcMuxConfig
from app.tui.keybindings import DocumentedKeybindings
from app.tui.types import FocusTarget, FocusWidget


class TUIState:
    def __init__(self, config: ProcMuxConfig):
        self.config: ProcMuxConfig = config
        self.zoomed_in: bool = False
        self.filter_mode: bool = False
        self.docs_open: bool = False
        self.quitting: bool = False
        self._focus_targets: List[FocusTarget] = []
        self._modal_open: bool = False
        self._modal_keybindings: DocumentedKeybindings = DocumentedKeybindings()

    @property
    def focus_targets(self) -> List[FocusTarget]:
        return self._focus_targets

    @property
    def modal_open(self) -> bool:
        return self._modal_open

    @property
    def modal_keybindings(self) -> DocumentedKeybindings:
        return self._modal_keybindings

    def get_focus_element(self, widget: FocusWidget) -> Optional[Any]:
        return next((ft.element for ft in self._focus_targets if ft.widget == widget), None)

    def register_focusable_element(self, target: FocusTarget):
        self._focus_targets.append(target)

    def deregister_focusable_element(self, widget: FocusWidget):
        self._focus_targets = [fe for fe in self._focus_targets if fe.widget != widget]

    def open_modal(self, kb: DocumentedKeybindings = DocumentedKeybindings()):
        self._modal_open = True
        self._modal_keybindings = kb

    def close_modal(self):
        self._modal_open = False
        self._modal_keybindings = DocumentedKeybindings()
