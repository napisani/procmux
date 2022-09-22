import curses
import os

import pyte


def do():
    screen = pyte.Screen(40, 12)
    stream = pyte.Stream(screen)
    stream.feed("Hello World!")
    print(screen.display)


def do2():
    """Test TUI.

    Args:
        keys (str): keys to be send to the TUI.
        assertion (Callable): function to run the
                              assertions for the keys
                              to be tested.
    """
    pid, f_d = os.forkpty()
    if pid == 0:
        curses.wrapper(TUI)
    else:
        screen = pyte.Screen(80, 24)
        stream = pyte.ByteStream(screen)
        ### SEND KEYS
        # send keys char-wise to TUI
        for key in keys:
            os.write(f_d, str.encode(key))
        ### END
        while True:
            try:
                [f_d], _, _ = select.select(
                    [f_d], [], [], 1)
            except (KeyboardInterrupt, ValueError):
                break
            else:
                try:
                    data = os.read(f_d, 1024)
                    stream.feed(data)
                except OSError:
                    break
        for line in screen.display:
            print(line)
if __name__ == "__main__":
    do()
