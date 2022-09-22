import os
import sys


def do():
    pid, fd = os.forkpty()

    if pid == 0:
        # child
        os.execlp('vim', "vim")
    else:
        # parent
        print
        os.read(fd, 1000)

        c = os.read(fd, 1)
        while c:
            c = os.read(fd, 1)
            sys.stdout.write(c.decode('utf8'))


if __name__ == "__main__":
    do()
