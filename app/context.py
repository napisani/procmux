from app.config import ProcMuxConfig
from app.tui_state import TUIState


class NeverBootstrapped(Exception):
    pass


class ProcMuxContext:
    """
    ProxMuxContext is a singleton object that acts as a global handle to both
    shared TUI state and all parsed configuration points

    the ProxMuxContext must be bootstrapped before the TUI app is started
    """
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(ProcMuxContext, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._instance:
            self._config = None
            self.tui_state = TUIState()

    def bootstrap(self, config: ProcMuxConfig):
        self._config = config
        self.tui_state = TUIState()

    def validate_init(self):
        if not self._config:
            raise NeverBootstrapped('bootstrap must be called before the processes service can be used')

    @property
    def config(self) -> ProcMuxConfig:
        self.validate_init()
        return self._config
