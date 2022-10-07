from typing import Any, Callable, List, Optional

from prompt_toolkit.key_binding import KeyBindings

from app.tui.types import KeybindingDocumentation


class DocumentedKeybindings(KeyBindings):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.help_docs: List[KeybindingDocumentation] = []

    def add_keybinding_help_doc(self, label: str, keys: List[str]):
        if keys:
            self.help_docs.append(KeybindingDocumentation(label=label, help=keys[0]))

    def register_configured_keybinding_sans_event(self,
                                                  keys: List[str],
                                                  handler: Callable[[], None],
                                                  help_label: Optional[str] = None,
                                                  ):
        self.register_configured_keybinding(keys, lambda _: handler(), help_label=help_label)

    def register_configured_keybinding(self,
                                       keys: List[str],
                                       handler: Callable[[Any], None],
                                       help_label: Optional[str] = None
                                       ):
        if 'disabled' in keys:
            return

        for keybinding in keys:
            @self.add(keybinding)
            def _(event) -> None:
                handler(event)

        if help_label:
            self.add_keybinding_help_doc(label=help_label, keys=keys)
