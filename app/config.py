from dataclasses import dataclass, field, fields
import os
from typing import Dict, List, Literal, Optional, OrderedDict, Union

import hiyapyco
from prompt_toolkit.layout import D, Dimension
from prompt_toolkit.output import ColorDepth

from app.util.interpolation import Interpolation, parse_interpolations


class MisconfigurationError(Exception):
    pass


@dataclass
class ProcessConfig:
    """
    shell:(str) command to run (exactly one of shell or cmd must be provided).
    cmd: (list) Array of command and args to run (exactly one of shell or cmd must be provided).
    cwd:(str) Set working directory for the process.
    env: (Dict[str,str]) - Set env variables. Object keys are variable names.
    add_path: string|array - Add entries to the PATH environment variable.
    autostart: bool - Start process when procmux starts.
    stop: "SIGINT"|"SIGTERM"|"SIGKILL" - default will SIGKILL
    """
    autostart: bool = False
    shell: Optional[str] = None
    cmd: Optional[List[str]] = None
    cwd: str = os.getcwd()
    stop: str = "SIGKILL"
    env: Optional[Dict[str, Optional[str]]] = None
    add_path: Optional[Union[str, List[str]]] = None
    description: Optional[str] = None
    docs: Optional[str] = None
    categories: Optional[List[str]] = None
    meta_tags: Optional[List[str]] = None

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self.cmd and not self.shell:
            raise MisconfigurationError('shell or cmd is required for every proc definition')

    @property
    def interpolations(self) -> List[Interpolation]:
        if self.cmd:
            return parse_interpolations(*self.cmd)
        return parse_interpolations(self.shell)


@dataclass
class LayoutConfig:
    hide_help: bool = False
    hide_process_description_panel: bool = False
    processes_list_width: int = 31
    sort_process_list_alpha: bool = True
    category_search_prefix: str = 'cat:'
    field_replacement_prompt: str = '__FIELD_NAME__ ⮕  '


@dataclass
class StyleConfig:
    selected_process_color: str = 'ansiblack'
    selected_process_bg_color: str = 'ansimagenta'
    unselected_process_color: str = 'ansiblue'
    status_running_color: str = 'ansigreen'
    status_stopped_color: str = 'ansired'
    placeholder_terminal_bg_color: str = '#1a1b26'
    pointer_char: str = '▶'
    style_classes: Optional[Dict[str, str]] = None
    color_level: \
        Optional[
            Union[Literal['monochrome'], Literal['ansicolors'], Literal['256colors'], Literal['truecolors']]] = None

    @property
    def color_depth(
            self
    ) -> Union[Literal['DEPTH_1_BIT'], Literal['DEPTH_4_BIT'], Literal['DEPTH_8_BIT'], Literal['DEPTH_24_BIT']]:
        if self.color_level == 'monochrome':
            return ColorDepth.MONOCHROME
        if self.color_level == 'ansicolors':
            return ColorDepth.ANSI_COLORS_ONLY
        if self.color_level == '256colors':
            return ColorDepth.DEFAULT
        return ColorDepth.TRUE_COLOR

    @property
    def width_100(self) -> Dimension:
        return D(preferred=100 * 100)

    @property
    def height_100(self) -> Dimension:
        return D(preferred=100 * 100)


@dataclass
class KeybindingConfig:
    quit: List[str] = field(default_factory=lambda: ['q'])
    filter: List[str] = field(default_factory=lambda: ['/'])
    submit_filter: List[str] = field(default_factory=lambda: ['enter'])
    next_input: List[str] = field(default_factory=lambda: ['tab', 'down'])
    previous_input: List[str] = field(default_factory=lambda: ['s-tab', 'up'])
    submit_dialog: List[str] = field(default_factory=lambda: ['enter'])
    cancel_dialog: List[str] = field(default_factory=lambda: ['escape'])
    start: List[str] = field(default_factory=lambda: ['s'])
    stop: List[str] = field(default_factory=lambda: ['x'])
    up: List[str] = field(default_factory=lambda: ['up', 'k'])
    down: List[str] = field(default_factory=lambda: ['down', 'j'])
    switch_focus: List[str] = field(default_factory=lambda: ['c-w'])
    zoom: List[str] = field(default_factory=lambda: ['c-z'])
    docs: List[str] = field(default_factory=lambda: ['?'])
    toggle_scroll: List[str] = field(default_factory=lambda: ['c-s'])

    def __post_init__(self):
        for keybinding_field in fields(KeybindingConfig):
            keybinding = getattr(self, keybinding_field.name)
            if type(keybinding) == str:
                keybinding = [keybinding]
                setattr(self, keybinding_field.name, keybinding)


@dataclass
class ProcMuxConfig:
    procs: Dict[str, ProcessConfig] = field(default_factory=lambda: {})
    style: StyleConfig = StyleConfig()
    keybinding: KeybindingConfig = KeybindingConfig()
    shell_cmd: List[str] = field(default_factory=lambda: [os.environ['SHELL'], '-c'])
    layout: LayoutConfig = LayoutConfig()
    log_file: Optional[str] = None
    enable_mouse: bool = True

    def __post_init__(self):
        def is_dict_like(obj):
            return type(obj) == dict or isinstance(obj, OrderedDict)

        if is_dict_like(self.procs):
            process_config_data = dict()
            for proc_key in self.procs:
                process_config_data[proc_key] = ProcessConfig(**self.procs[proc_key])
            self.procs = process_config_data
        if is_dict_like(self.style):
            self.style = StyleConfig(**self.style)
        if is_dict_like(self.keybinding):
            self.keybinding = KeybindingConfig(**self.keybinding)
        if is_dict_like(self.layout):
            self.layout = LayoutConfig(**self.layout)


def parse_config(config_file: str,
                 override_config_file: Optional[str] = None) -> ProcMuxConfig:
    config_files = [config_file]
    if override_config_file:
        config_files.append(override_config_file)

    config_dict = hiyapyco.load(*config_files, method=hiyapyco.METHOD_SIMPLE,
                                failonmissingfiles=True)
    return ProcMuxConfig(**config_dict)
