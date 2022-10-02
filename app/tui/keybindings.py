from typing import Any, Callable, List

from prompt_toolkit.key_binding import KeyBindings

from app.config import ProcMuxConfig


def register_configured_keybinding_no_event(keys: List[str],
                                            handler: Callable[[], None],
                                            kb: KeyBindings
                                            ) -> KeyBindings:
    def _handler(_) -> None:
        handler()
    return register_configured_keybinding(keys, _handler, kb)


def register_configured_keybinding(keys: List[str], handler: Callable[[Any], None], kb: KeyBindings) -> KeyBindings:
    if 'disabled' in keys:
        return kb

    for keybinding in keys:
        @kb.add(keybinding)
        def _(event) -> None:
            handler(event)

    return kb


def register_app_wide_configured_keybindings(config: ProcMuxConfig,
                                             switch_focus: Callable[[], None],
                                             zoom: Callable[[], None],
                                             toggle_scroll: Callable[[], None],
                                             kb: KeyBindings
                                             ) -> KeyBindings:
    kb = register_configured_keybinding_no_event(config.keybinding.switch_focus, switch_focus, kb)
    kb = register_configured_keybinding_no_event(config.keybinding.zoom, zoom, kb)
    kb = register_configured_keybinding_no_event(config.keybinding.toggle_scroll, toggle_scroll, kb)
    return kb
