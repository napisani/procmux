import argparse
import os
import sys

parser = argparse.ArgumentParser(description="procmux")

sub_parsers = parser.add_subparsers(help='sub-command help', dest='subcommand')
parser_start = sub_parsers.add_parser('start', help='start procmux')
parser_start.add_argument('--config', required=False)
parser_start.add_argument('--config-override', required=False)

parser_signal_start = sub_parsers.add_parser(
    'signal-start',
    help=
    'send a start signal to processes managed by a running procmux instance')
parser_signal_start.add_argument('--name',
                                 type=str,
                                 help='the process name to send the signal to',
                                 required=True)
parser_signal_start.add_argument('--config', required=False)
parser_signal_start.add_argument('--config-override', required=False)

parser_signal_stop = sub_parsers.add_parser(
    'signal-stop',
    help='send a stop signal to processes managed by a running procmux instance'
)
parser_signal_stop.add_argument('--name',
                                type=str,
                                help='the process name to send the signal to',
                                required=True)
parser_signal_stop.add_argument('--config', required=False)
parser_signal_stop.add_argument('--config-override', required=False)

parser_signal_restart = sub_parsers.add_parser(
    'signal-restart',
    help=
    'send a restart signal to processes managed by a running procmux instance')
parser_signal_restart.add_argument(
    '--name',
    type=str,
    help='the process name to send the signal to',
    required=True)
parser_signal_restart.add_argument('--config', required=False)
parser_signal_restart.add_argument('--config-override', required=False)

parser_signal_restart_running = sub_parsers.add_parser(
    'signal-restart-running',
    help=
    'send a restart signal to all running processes managed by a running procmux instance'
)
parser_signal_restart_running.add_argument('--config', required=False)
parser_signal_restart_running.add_argument('--config-override', required=False)

parser_signal_stop_running = sub_parsers.add_parser(
    'signal-stop-running',
    help=
    'send a stop signal to all running processes managed by a running procmux instance'
)
parser_signal_stop_running.add_argument('--config', required=False)
parser_signal_stop_running.add_argument('--config-override', required=False)

if len(sys.argv) == 1 or sys.argv[1] not in [
        'start', 'signal-start', 'signal-stop', 'signal-restart',
        'signal-restart-running', 'signal-stop-running'
]:
    sys.argv.insert(1, 'start')
    cli_args = parser.parse_args(sys.argv[1:])
else:
    cli_args = parser.parse_args()

if not cli_args.config:
    potential_defaults = [
        'procmux-config.yml', 'procmux-config.yaml', 'procmux.yml',
        'procmux.yaml'
    ]
    for potential_default in potential_defaults:
        if os.path.exists(potential_default):
            cli_args.config = potential_default
            break
    if not cli_args.config:
        raise RuntimeError(
            f"{', '.join(potential_defaults)}  config files were not found in the current directory, please use --config to pass a procmux configuration file."
        )
