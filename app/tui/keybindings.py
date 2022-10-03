from typing import Any, Callable, List, Optional

from prompt_toolkit.key_binding import KeyBindings

from app.config import ProcMuxConfig
from app.tui.state import KeybindingDocumentation


class DocumentedKeybindings(KeyBindings):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.help_docs: List[KeybindingDocumentation] = []

    def add_keybinding_help_doc(self,
                                label: str,
                                keys: List[str],
                                should_show_help: Optional[Callable[[], bool]] = None):
        if keys:
            self.help_docs.append(KeybindingDocumentation(
                label=label,
                help=keys[0],
                should_display=should_show_help if should_show_help else (lambda: True)))


def register_configured_keybinding_no_event(
        keys: List[str],
        handler: Callable[[], None],
        kb: DocumentedKeybindings,
        help_label: Optional[str] = None,
        should_show_help: Optional[Callable[[], bool]] = None) -> DocumentedKeybindings:
    def _handler(_) -> None:
        handler()

    return register_configured_keybinding(keys, _handler, kb,
                                          help_label=help_label,
                                          should_show_help=should_show_help)


def register_configured_keybinding(
        keys: List[str],
        handler: Callable[[Any], None],
        kb: DocumentedKeybindings,
        help_label: Optional[str] = None,
        should_show_help: Optional[Callable[[], bool]] = None) -> DocumentedKeybindings:
    if 'disabled' in keys:
        return kb

    for keybinding in keys:
        @kb.add(keybinding)
        def _(event) -> None:
            handler(event)
    if help_label:
        kb.add_keybinding_help_doc(label=help_label,
                                   keys=keys,
                                   should_show_help=should_show_help)

    return kb


def register_app_wide_configured_keybindings(config: ProcMuxConfig,
                                             switch_focus: Callable[[], None],
                                             zoom: Callable[[], None],
                                             toggle_scroll: Callable[[], None],
                                             kb: DocumentedKeybindings) -> DocumentedKeybindings:
    kb = register_configured_keybinding_no_event(
        config.keybinding.switch_focus,
        switch_focus,
        kb,
        help_label='switch_focus')
    kb = register_configured_keybinding_no_event(
        config.keybinding.zoom,
        zoom,
        kb,
        help_label='zoom')
    kb = register_configured_keybinding_no_event(
        config.keybinding.toggle_scroll,
        toggle_scroll,
        kb,
        help_label='toggle scroll')
    return kb
