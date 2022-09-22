from typing import Dict

from app.config import ProcMuxConfig
from app.exec import ProcessManager
from app.tui_state import TUIState


class NeverBootstrapped(Exception):
    pass


class ProcMuxContext:
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(ProcMuxContext, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._instance:
            self._config = None
            self._proc_managers = dict()
            self.tui_state = TUIState()

    def bootstrap(self, config: ProcMuxConfig):
        self._config = config
        self._proc_managers = {
            proc_name: ProcessManager(proc_config) for proc_name, proc_config in
            self._config.procs.items()
        }
        self.tui_state = TUIState()

    def validate_init(self):
        if not self._config or not self._proc_managers:
            raise NeverBootstrapped('bootstrap must be called before the processes service can be used')

    @property
    def config(self) -> ProcMuxConfig:
        self.validate_init()
        return self._config

    @property
    def proc_managers(self) -> Dict[str, 'ProcessManager']:
        self.validate_init()
        return self._proc_managers
