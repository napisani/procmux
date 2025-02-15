import logging
import sys

from procmux.args import cli_args
from procmux.config import ProcMuxConfig, parse_config
from procmux.log import formatter, logger
from procmux.server.client import SignalClient


def run_app(cfg: ProcMuxConfig):
    if cfg.log_file:
        file_handler = logging.FileHandler(cfg.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    from procmux.tui.app import start_tui

    start_tui(cfg)


def start_cli():
    config = parse_config(cli_args.config, cli_args.config_override)
    if cli_args.subcommand == "start":
        run_app(config)
    else:
        try:
            signal_client = SignalClient(config)
            if cli_args.subcommand == "signal-start":
                name = cli_args.name
                signal_client.start_process(name)
            elif cli_args.subcommand == "signal-stop":
                name = cli_args.name
                signal_client.stop_process(name)
            elif cli_args.subcommand == "signal-restart":
                name = cli_args.name
                signal_client.restart_process(name)
            elif cli_args.subcommand == "signal-restart-running":
                signal_client.restart_running_processes()
            elif cli_args.subcommand == "signal-stop-running":
                signal_client.stop_running_processes()
        except ValueError as e:
            print(e)
            sys.exit(1)
