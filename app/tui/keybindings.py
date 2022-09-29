from typing import Callable, Optional

from prompt_toolkit.key_binding import KeyBindings

from app.context import ProcMuxContext
from app.log import logger
from app.tui.focus import FocusManager


def register_configured_keybinding(key_config_attr: str, handler: Callable,
                                   kb: Optional[KeyBindings] = None) -> KeyBindings:
    if not kb:
        kb = KeyBindings()
    ctx = ProcMuxContext()
    all_keys = getattr(ctx.config.keybinding, key_config_attr)
    if 'disabled' in all_keys:
        return kb

    for keybinding in all_keys:
        @kb.add(keybinding)
        def _toggle_scroll(event) -> None:
            handler(event)

    return kb


def register_app_wide_configured_keybindings(focus_manager: FocusManager,
                                             kb: Optional[KeyBindings] = None) -> KeyBindings:
    if not kb:
        kb = KeyBindings()
    ctx = ProcMuxContext()

    def _switch_focus(_event):
        logger.info('in _switch_focus')
        if not focus_manager.is_focused_on_free_form_input():
            focus_manager.toggle_sidebar_terminal_focus()

    kb = register_configured_keybinding('switch_focus', _switch_focus, kb)

    def _zoom(_event):
        logger.info('in _zoom')
        if not focus_manager.is_focused_on_free_form_input():
            focus_manager.toggle_zoom()

    kb = register_configured_keybinding('zoom', _zoom, kb)

    def _toggle_scroll(_event) -> None:
        logger.info('in _toggle_scroll')
        proc_idx = ctx.tui_state.selected_process_idx
        if not focus_manager.is_focused_on_free_form_input() and proc_idx > -1:
            scroll_mode_on = ctx.tui_state.terminal_managers[proc_idx].toggle_scroll_mode()
            if not scroll_mode_on:
                focus_manager.focus_to_sidebar()

    kb = register_configured_keybinding('toggle_scroll', _toggle_scroll, kb)
    return kb
