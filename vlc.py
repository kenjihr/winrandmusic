import requests
import subprocess
import os
import time
import pathlib
import log

_config = {
    "command": ["C:\\Program Files\\VideoLAN\\VLC\\vlc.exe", "--random"],
    "http_host": "127.0.0.1",
    "http_port": 28080,
    "http_password": "12345"
}

_popen = None

_logger = log.initLogger(__name__)


def set_param(command=None, http_host=None, http_port=None, http_password=None):
    global _config
    if command is not None:
        _config['command'] = command
    if http_host is not None:
        _config['http_host'] = http_host
    if http_port is not None:
        _config['http_port'] = http_port
    if http_password is not None:
        _config['http_password'] = http_password


def start_app():
    global _popen
    args = [f"--http-host={_config['http_host']}", f"--http-port={_config['http_port']}", f"--http-password={_config['http_password']}"]
    kill_app()
    _popen = subprocess.Popen(_config['command'] + args)

    for _ in range(10):
        r = get_status()
        if r.status_code == 200:
            break
        time.sleep(0.5)


def kill_app():
    global _popen
    if _popen is not None:
        _popen.kill()
        _popen = None


def find_app():
    ret = os.system('tasklist /FI "imagename eq vlc.exe" | findstr vlc.exe > NUL')
    return ret == 0


def _get_uri_from_windows_path(path):
    return pathlib.Path(path).as_uri()


def _request_status(query=None):
    url = f"http://:{_config['http_password']}@{_config['http_host']}:{_config['http_port']}/requests/status.json"
    if query and len(query) > 0:
        url = url + query

    r = requests.get(url, timeout=(5.0, 10.0))
    r.encoding = 'utf-8'  # assume charset is utf-8
    if r.status_code != 200:
        _logger.info("error: vlc bad status code:%d", r.status_code)
        _logger.debug(r.text)
    return r


def _request_command(command):
    query = f"?command={command}"
    return _request_status(query)


def play():
    _request_command("pl_play")


def stop():
    _request_command("pl_stop")


def set_playlists(paths):
    stop()

    # clear playlist
    _request_command("pl_empty")

    # add playlist
    lst = paths
    if not isinstance(lst, list):
        lst = [lst]
    for path in lst:
        uri = _get_uri_from_windows_path(path)
        _request_command(f"in_enqueue&input={uri}")


def set_volume(volume):
    _request_command(f"volume&val={volume}")


def get_status():
    return _request_status()

def set_debug_level():
    log.setDebugLevel(__name__)