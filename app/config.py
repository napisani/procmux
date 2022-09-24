#!/usr/bin/env python
from dataclasses import dataclass, field, fields
import io
import os
from typing import Dict, List, Optional, Union

import yaml


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
    env: Dict[str, Optional[str]] = None
    add_path: Optional[Union[str, List[str]]] = None
    description: Optional[str] = None

    def __post_init__(self):
        self.validate()

    def validate(self):
        if not self.cmd and not self.shell:
            raise MisconfigurationError('shell or cmd is required for every proc definition')


@dataclass
class LayoutConfig:
    hide_help: bool = False
    hide_process_description_panel: bool = False
    processes_list_width: int = 31
    sort_process_list_alpha: bool = True


@dataclass
class StyleConfig:
    selected_process_color: str = 'ansiblack'
    selected_process_bg_color: str = 'ansimagenta'
    unselected_process_color: str = 'ansiblue'
    status_running_color: str = 'ansigreen'
    status_stopped_color: str = 'ansired'
    placeholder_terminal_bg_color: str = '#1a1b26'


@dataclass
class KeybindingConfig:
    quit: List[str] = field(default_factory=lambda: ['q'])
    filter: List[str] = field(default_factory=lambda: ['/'])
    submit_filter: List[str] = field(default_factory=lambda: ['enter'])
    start: List[str] = field(default_factory=lambda: ['s'])
    stop: List[str] = field(default_factory=lambda: ['x'])
    up: List[str] = field(default_factory=lambda: ['up', 'k'])
    down: List[str] = field(default_factory=lambda: ['down', 'j'])
    switch_focus: List[str] = field(default_factory=lambda: ['c-w'])
    zoom: List[str] = field(default_factory=lambda: ['z'])

    def __post_init__(self):
        for keybinding_field in fields(KeybindingConfig):
            keybinding = getattr(self, keybinding_field.name)
            if type(keybinding) == str:
                keybinding = [keybinding]
                setattr(self, keybinding_field.name, keybinding)


@dataclass
class ProcMuxConfig:
    procs: Optional[Dict[str, ProcessConfig]]
    style: StyleConfig = StyleConfig()
    keybinding: KeybindingConfig = KeybindingConfig()
    shell_cmd: List[str] = field(default_factory=lambda: [os.environ['SHELL'], '-c'])
    layout: LayoutConfig = LayoutConfig()
    log_file: Optional[str] = None

    def __post_init__(self):
        if type(self.procs) == dict:
            process_config_data = dict()
            for proc_key in self.procs:
                process_config_data[proc_key] = ProcessConfig(**self.procs[proc_key])
            self.procs = process_config_data
        if type(self.style) == dict:
            self.style = StyleConfig(**self.style)
        if type(self.keybinding) == dict:
            self.keybinding = KeybindingConfig(**self.keybinding)
        if type(self.layout) == dict:
            self.layout = LayoutConfig(**self.layout)


def parse_config(config_file: Union[io.TextIOWrapper, io.FileIO, str]) -> ProcMuxConfig:
    if isinstance(config_file, io.TextIOWrapper):
        return ProcMuxConfig(**yaml.safe_load(config_file))
    with open(config_file, 'r') as f:
        return ProcMuxConfig(**yaml.safe_load(f))


def parse_config_from_yaml_string(yaml_config: str) -> ProcMuxConfig:
    return ProcMuxConfig(**yaml.safe_load(yaml_config))
