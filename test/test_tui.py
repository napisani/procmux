import os
import select
import tempfile

import pyte

from procmux.__main__ import run_app
from procmux.config import parse_config


def _get_config_yaml(log_file: str) -> str:
    config_yaml = f"""\
    layout:
      hide_help: false
    keybinding:
      switch_focus: 'w'
      up: 'k'
      down: 'j'
    procs:
      "tail log":
        shell: "tail -f {log_file}"
        autostart: true
        description: 'tail the app log'
        docs: long description for tail log
        meta_tags:
          - 'follow'
      "print envs":
        shell: "echo $SOME_TEST"
        description: 'this command will print env vars that are configured in the child pid'
        env:
          SOME_TEST: "ENV_VARS_ARE_WORKING"
        categories:
          - 'echo'
      "vim":
        shell: "vim"
        autostart: false
        description: 'start vim'
      "test long running proc":
        shell: "echo 'some text here' && sleep 3 && echo 'still running'  && sleep 3 && echo 'final text'"
        autostart: false
        description: 'print a using sleeps in between'
        categories:
          - 'echo'
      "interpolate":
        shell: "echo '<first_echo:some default>' && echo '<second_echo>'"
        autostart: false
        description: 'test interpolation'

    """
    return config_yaml


def preform_test_within_tui(keys, assertion):
    """Test TUI."""
    # create pseudo-terminal
    pid, f_d = os.forkpty()
    if pid == 0:
        # child process spawns TUI
        with tempfile.NamedTemporaryFile() as yaml_tmp:
            with tempfile.NamedTemporaryFile() as log_tmp:
                config_yaml = _get_config_yaml(log_tmp.name)
                yaml_tmp.write(config_yaml.encode('utf8'))
                yaml_tmp.flush()
                config = parse_config(yaml_tmp.name)
                run_app(config)

    else:
        screen = pyte.Screen(100, 30)
        stream = pyte.ByteStream(screen)
        for key in keys:
            print(f'sending key input: {key}')
            os.write(f_d, str.encode(key))
        # scrape pseudo-terminal's screen
        while True:
            try:
                [f_d], _, _ = select.select(
                    [f_d], [], [], 1)
            except (KeyboardInterrupt, ValueError):
                # either test was interrupted or the
                # file descriptor of the child process
                # provides nothing to be read
                break
            else:
                try:
                    # scrape screen of child process
                    data = os.read(f_d, 1024)
                    stream.feed(data)
                except OSError:
                    # reading empty
                    break
        print('\n')
        for line in screen.display:
            print(line)

        assertion(screen)


def join_screen_to_str(screen) -> str:
    return "\n".join(screen.display)


def test_tui_shows_process_list_help():
    def assert_process_list_help_bar(screen):
        full_screen = join_screen_to_str(screen)
        assert '<s> start' in full_screen
        assert '<x> stop' not in full_screen
        assert '<q> quit' in full_screen

    preform_test_within_tui(keys=[], assertion=assert_process_list_help_bar)


def test_tui_shows_terminal_help():
    def assert_terminal_help_bar(screen):
        full_screen = join_screen_to_str(screen)
        assert '<s> start' not in full_screen
        assert '<x> stop' not in full_screen
        assert '<w> switch' in full_screen

    preform_test_within_tui(keys=['j', 'j', 'w'], assertion=assert_terminal_help_bar)


def test_tui_filter():
    def assert_filter(screen):
        full_screen = join_screen_to_str(screen)
        assert '<s> start' not in full_screen
        assert '<enter> submit filter' in full_screen
        assert 'test long running proc' in full_screen
        assert 'tail log' not in full_screen

    preform_test_within_tui(keys=['/', *list('test long run')], assertion=assert_filter)


def test_tui_filter_cancel():
    def assert_filter(screen):
        full_screen = join_screen_to_str(screen)
        assert '<s> start' in full_screen
        assert '<enter> submit filter' not in full_screen
        assert 'test long running proc' in full_screen
        assert 'tail log' in full_screen

    preform_test_within_tui(keys=['/', *list('test long run'), '/'], assertion=assert_filter)


def test_tui_env_vars_in_child_pid():
    def assert_env_vars_printed(screen):
        full_screen = join_screen_to_str(screen)
        assert 'ENV_VARS_ARE_WORKING' in full_screen

    preform_test_within_tui(keys=['/', *list('print env'), '\n', 's'], assertion=assert_env_vars_printed)


def test_tui_filter_for_missing_process_shows_no_results():
    def assert_no_results(screen):
        full_screen = join_screen_to_str(screen)
        assert 'tail log' not in full_screen
        assert 'print envs' not in full_screen
        assert 'vim' not in full_screen
        assert 'test long running proc' not in full_screen

    preform_test_within_tui(keys=['/', *list('NEVER'), '\n', 'j'], assertion=assert_no_results)


def test_tui_filter_against_category():
    def assert_no_results(screen):
        full_screen = join_screen_to_str(screen)
        assert 'test long running proc' in full_screen
        assert 'print envs' in full_screen
        assert 'vim' not in full_screen

    preform_test_within_tui(keys=['/', *list('cat:echo'), '\n', 'j'], assertion=assert_no_results)


def test_tui_filter_against_meta_tags():
    def assert_no_results(screen):
        full_screen = join_screen_to_str(screen)
        assert 'test long running proc' not in full_screen
        assert 'print envs' not in full_screen
        assert 'vim' not in full_screen
        assert 'tail log' in full_screen

    preform_test_within_tui(keys=['/', *list('follow'), '\n', 'j'], assertion=assert_no_results)


def test_long_docs_get_displayed():
    def assert_no_results(screen):
        full_screen = join_screen_to_str(screen)
        assert 'long description for tail log' in full_screen
        assert 'print envs' not in full_screen

    preform_test_within_tui(keys=['/', *list('tail log'), '\n', 'j', '?'], assertion=assert_no_results)


def test_tui_autostart():
    def assert_autostart(screen):
        for line in screen.display:
            if "tail log" in line:
                assert "UP" in line
                break
        else:
            raise RuntimeError('Active tail log process not found')

    preform_test_within_tui(keys=[], assertion=assert_autostart)
