from app.config import ProcessConfig
from app.exec import ProcessManager


def test_process_manager_exec_long_running_and_stop():
    proc_config = ProcessConfig(shell="tail -f /dev/null")
    manager = ProcessManager(proc_config)
    assert not manager.is_running()
    manager.start()
    assert manager.is_running()
    manager.send_stop_signal()
    manager.sync()
    assert not manager.is_running()


def test_pty():
    proc_config = ProcessConfig(shell="echo 'test'")
    manager = ProcessManager(proc_config)
    assert not manager.is_running()
    manager.start_pty()


if __name__ == '__main__':
    test_pty()
