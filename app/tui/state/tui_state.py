from typing import Any, List, Optional

from app.config import ProcMuxConfig
from app.tui.types import FocusTarget, FocusWidget


class TUIState:
    def __init__(self, config: ProcMuxConfig):
        self.config: ProcMuxConfig = config
        self.zoomed_in: bool = False
        self.filter_mode: bool = False
        self.docs_open: bool = False
        self.quitting: bool = False
        self._focus_targets: List[FocusTarget] = []
        self._interpolating: bool = False
        self._command_form: Optional[Any] = None

    @property
    def focus_targets(self) -> List[FocusTarget]:
        return self._focus_targets

    @property
    def interpolating(self) -> bool:
        return self._interpolating

    @property
    def command_form(self) -> Optional[Any]:
        return self._command_form

    def get_focus_element(self, widget: FocusWidget) -> Optional[Any]:
        return next((ft.element for ft in self._focus_targets if ft.widget == widget), None)

    def register_focusable_element(self, target: FocusTarget):
        self._focus_targets.append(target)

    def deregister_focusable_element(self, widget: FocusWidget):
        self._focus_targets = [fe for fe in self._focus_targets if fe.widget != widget]

    def start_interpolating(self, command_form: Any):
        self._command_form = command_form
        self._interpolating = True

    def stop_interpolating(self):
        self._interpolating = False
        self._command_form = None
