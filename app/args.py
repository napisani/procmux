import argparse

import os

parser = argparse.ArgumentParser(description="procmux-tui")
parser.add_argument('--config', required=False)
parser.add_argument('--config-override', required=False)
cli_args = parser.parse_args()
if not cli_args.config:
    potential_defaults = [
            'procmux-config.yml', 
            'procmux-config.yaml', 
            'procmux.yml', 
            'procmux.yaml'
    ]
    for potential_default in potential_defaults:
        if os.path.exists(potential_default):
            cli_args.config = potential_default 
            break
    if not cli_args.config:
        raise RuntimeError(f"{', '.join(potential_defaults)}  config files were not found in the current directory, please use --config to pass a procmux configuration file.") 


