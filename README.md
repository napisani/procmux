# procmux

a TUI utility for running multiple commands in parallel in easily switchable terminals

this app is heavily influenced by this TUI app: https://github.com/pvolok/mprocs

### The goals/use-cases:

procmux allows the user to run multiple commands in parallel and makes it
easy to view the output from each terminal session.
Procmux configuration files can be included in projects that have a series of commonly used scripts / long-running
processes.
is intended to make it easy for newcomers to a project to browse and run necessary commands, while also reducing the
need to manually spin up multiple terminal sessions for potentially long-running processes.
Alternatively, personal or system-wide procmux config files can be defined for browsing/running snippets or commonly
used shell
scripts.

![Alt Text](https://github.com/napisani/procmux/blob/main/demo.gif)

## Installation

```bash
# if you use pipx
pipx install procmux

# if you use pip
pip install procmux

# if you use brew
brew tap napisani/procmux
brew install procmux

```

## Usage

```bash
# standard usage
procmux --config /path/to/config.yaml

# with overriding config values
procmux --config /path/to/config.yaml --config-override /path/to/override-file.yaml
```

## Configuration

Here is a procmux configuration example with ALL available configuration points.
Only the `procs` section is required, the rest of the properties have defaults predefined:

procmux.yaml

```yaml
layout:
  # hide or show the help window that show all keybindings and actions at the bottom of the screen
  hide_help: false
  # hide or show the window second from the bottom that shows the full command name and the description
  hide_process_description_panel: false
  # the prompt_toolkit width of the sidebar (containing all the process names)
  processes_list_width: 31
  # whether to sort the process list alphabetically
  sort_process_list_alpha: True
  # used as the prefix for category filters of the process list
  category_search_prefix: 'cat:'
  # the prompt template to be rendered everytime a field replacement input box is rendered
  # __FIELD_NAME__ will be replaced by the field name defined in the replacement definition 
  # IE: `echo "<something>"`  # field name is 'something'
  field_replacement_prompt: '__FIELD_NAME__ ⮕  '
style:
  #foreground color of the process in the process list when it is selected
  selected_process_color: 'ansiblack'
  #background color of the process in the process list when it is selected
  selected_process_bg_color: 'ansimagenta'
  #foregroud color of the process in the process list when it is not selected
  unselected_process_color: 'ansiblue'
  #foregroud color of the process list status when the status is RUNNING
  status_running_color: 'ansigreen'
  #foregroud color of the process list status when the status is STOPPED
  status_stopped_color: 'ansired'
  #the color of the right panel (terminal panel) when no terminal is created/selected yet
  placeholder_terminal_bg_color: '#1a1b26'
  # show or hide the border around the terminal panel and side bar
  show_borders: true 
  # whether to show the scrollbar on the right side of the sidebar 
  show_scrollbar: true 
  #character used to indicate the current selection
  pointer_char: '▶'
  #override default style classes
  #https://github.com/prompt-toolkit/python-prompt-toolkit/blob/master/src/prompt_toolkit/styles/defaults.py
  style_classes:
    cursor-line: 'underline'
  #one of: monochrome | ansicolors | 256colors | truecolors
  color_level: 'truecolors'
keybinding:
  # a map of app actions to their respective key bindings.
  # each key combo in an action list is an alias for the same action.
  # IE up is fired when 'j' or the 'up arrow' is pressed
  # All modifiers for a keybinding should be included in the same list element IE: switch focus - 'c-w' (Control-W)
  quit:
    - q
  filter:
    - /
  submit_filter:
    - enter
  start:
    - s
  stop:
    - x
  up:
    - up
    - k
  down:
    - down
    - j
  docs:
    - ?
  switch_focus:
    - 'c-w'
  zoom:
    - 'c-z'
  # using a keybinding of 'disabled' will remove any keybinding entirely
  #zoom:
  #  - 'disabled'
  toggle_scroll:
    - 'c-s'
shell_cmd:
  # this is the command used for all 'procs' that are defined with a 'shell' property.
  # by default the configured "$SHELL" environment variable will be used.
  - '/bin/bash'
  - '-c'

# if this property is defined, the app will log all debug, info, error level logs to the designated file
log_file: /tmp/term.log
enable_mouse: true
procs:
  # each key will show up as its own process/script in the process list
  "tail log":
    # the shell command to run when this process is started
    shell: "tail -f /tmp/term.log"
    # whether to start this process when ProcMux starts
    autostart: true
    # a short description of what this process/command does - will be displayed at the bottom of the screen when selected
    description: 'tail the app log'
    # meta tags will be searched against for during process filtering
    # meta tags much match fully (unlike the process name itself, which is fuzzy matched)
    meta_tags:
      - "follow"
      - "-f"
  "print envs":
    shell: "echo $SOME_TEST"
    description: 'this command will print env vars that are configured in the child pid'
    #used for showing man page/documentation dialog when the docs keybinding is pressed
    docs: |
      <b>echo an env var set in the child pid</b>
      <style fg="ansigreen">first an env var is set in the child pid</style>
      <style fg="ansiblue">then the var is printed</style>
    # environment variables before the command/shell is invoked
    env:
      SOME_TEST: "AAAAAA"
  "vim":
    shell: "vim"
    autostart: false
    description: 'start vim'
    # categories can be used to view your process list by single groups using filters formatted
    # like this: `cat:<category name>` 
    # IE: `cat:edit` - this will show all processes that have a category 'edit'
    categories:
      - "edit"
    
      
  "long running print":
    shell: "echo 'some text here' && sleep 3 && echo 'still running'  && sleep 3 && echo 'final text'"
    autostart: false
    description: 'print a using sleeps in between'
  "print colors":
    shell: "./print_colors.sh"
    # used to change the directory that the command/process is started from
    cwd: "/Users/nick/code/procmux-tui"
    autostart: false
    description: 'test terminal colors'
  "just echo":
    # an example of using a specific CMD list instead of a shell string
    cmd:
      - '/bin/bash'
      - '-c'
      - 'echo "DONE!"'
    autostart: false
    description: 'run using cmd property'
  "interpolation":
    # processes can be defined with replaceable values in this format <field_name:default> or <field_name>
    # when processes with interpolated values are started, the user will be prompted to enter values for each field.
    # processes with interpolated values cannot be configured with 'autostart: true' 
    shell: "echo '<first_echo:some default>' && echo '<second_echo>'"
    autostart: false 
    description: 'test interpolation'

# these settings are used to control a signal server that can be used to send signals to procmux managed processes
# using another terminal or script. when the signal server is enabled, it will listen on the configured host and port
# for incoming signals. the signal server can be used to send signals to procmux managed processes without having procmux
# in focus.
# the procmux app can be used to send signals. Use any of the available procmux subcommands to send signals to the signal # server. IE: `procmux signal-stop --name 'long running print' --config /path/to/procmux.yaml`
signal_server:
  enable: true 
  host: 'localhost'
  port: 9792
```
