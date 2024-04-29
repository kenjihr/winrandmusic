import requests
import urllib.parse
import log

_api_key = "0000000000000000000000000000000"

_logger = log.initLogger(__name__)


def set_api_key(key):
    global _api_key
    _api_key = key


def forecast(q, lang=None):
    url = f"https://api.weatherapi.com/v1/forecast.json?key={_api_key}&q={urllib.parse.quote(q)}&days=1&aqi=no&alerts=no"
    if lang:
        url += f"&lang={lang}"

    r = requests.get(url, timeout=(5.0, 10.0))
    if r.status_code != 200:
        _logger.info("error: wetherapi bad status code:%d", r.status_code)
        _logger.debug(r.text)
    return r

def set_debug_level():
    log.setDebugLevel(__name__)