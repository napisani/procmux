from prompt_toolkit.application.application import sys
from app.__main__ import run_app
from app.config import parse_config
from app.args import cli_args
from app.server.client import SignalClient


def start_cli():
    config = parse_config(cli_args.config, cli_args.config_override)
    if cli_args.subcommand == 'start':
        run_app(config)
    else:
        try:
            signal_client = SignalClient(config)
            if cli_args.subcommand == 'signal-start':
                name = cli_args.name
                signal_client.start_process(name)
            elif cli_args.subcommand == 'signal-stop':
                name = cli_args.name
                signal_client.stop_process(name)
            elif cli_args.subcommand == 'signal-restart':
                name = cli_args.name
                signal_client.restart_process(name)
            elif cli_args.subcommand == 'signal-restart-running':
                signal_client.restart_running_processes()
            elif cli_args.subcommand == 'signal-stop-running':
                signal_client.stop_running_processes()
        except ValueError as e:
            print(e)
            sys.exit(1)





if __name__ == '__main__':
    start_cli()
