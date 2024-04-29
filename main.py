import datetime
import time
import os
import sys
import pathlib
import random
import argparse
import i18n
import system_volume
import vlc
import playlist
import weather_api
import speech_api
import config
import log

_logger = log.initLogger(__name__)
_current_playlist = None

APP_NAME = "wintimeweatherteller"


def _select_current_playlist(time_elapsed):
    sch = config.convert_playlist_schedule(config.config['media']['playlist'])
    p = None
    for i, t in enumerate(sch):
        if time_elapsed >= t['time']:
            if i == len(sch) - 1 or time_elapsed < sch[i + 1]["time"]:
                global _current_playlist
                if _current_playlist != t['playlist']:
                    _current_playlist = t['playlist']
                    return True
                else:
                    return False
    return False

def _start_current_playlist():
    p = None
    if _current_playlist:
        p = playlist.select_random_playlist(_current_playlist)
        _logger.info("playlist: %s", p)
    
    if p:
        vlc.set_playlists(p)
        vlc.play()
    else:
        vlc.stop()


def _set_random_locale():
    index = random.randint(0, len(config.config['locales']) - 1)
    locale = config.config['locales'][index]
    i18n.set('locale', locale)


def _set_speech_voice():
    speech_api.set_voice(i18n.t('message.speechapi_language'))


def _set_speech_volume(volume):
    speech_api.set_volume(volume)


def _speech_text(text):
    speech_api.speak(text)


def _speech_time():
    now = datetime.datetime.now()

    text_date = i18n.t('message.speak_date')
    text_date = text_date.replace("{MONTH}", str(now.month))
    text_date = text_date.replace("{DATE}", str(now.day))
    text_date = text_date.replace("{WEEKDAY}", i18n.t("message.weekday_" + str(now.weekday())))

    text_time = i18n.t('message.speak_time')
    text_time = text_time.replace("{HOUR}", str(now.hour))
    text_time = text_time.replace("{MINUTE}", str(now.minute))

    _logger.debug("time: %s %s", text_date, text_time)
    _speech_text(text_date + ' ' + text_time)


def _round_temparature(temp):
    return str(int(temp + 0.5))


def _get_weather():
    data = {}
    for lang in config.config['locales']:
        if lang not in data:
            data[lang] = None
            try:
                r = weather_api.forecast(config.config['weather']['q'], i18n.t("message.weatherapi_language", locale=lang)).json()
                text = i18n.t('message.speak_weather', locale=lang)
                text = text.replace("{CONDITION}", r["forecast"]["forecastday"][0]["day"]["condition"]["text"])
                text = text.replace("{MINTEMP_C}", _round_temparature(r["forecast"]["forecastday"][0]["day"]["mintemp_c"]))
                text = text.replace("{MAXTEMP_C}", _round_temparature(r["forecast"]["forecastday"][0]["day"]["maxtemp_c"]))
                text = text.replace("{MINTEMP_F}", _round_temparature(r["forecast"]["forecastday"][0]["day"]["mintemp_f"]))
                text = text.replace("{MAXTEMP_F}", _round_temparature(r["forecast"]["forecastday"][0]["day"]["maxtemp_f"]))
                data[lang] = text
            except Exception as e:
                _logger.exception("%s %s", type(e), e)
    return data


def _calcurate_volume_sub(time_elapsed, time0, time1, v0, v1):
    if time_elapsed >= time1 or time0 == time1:
        return v1
    return float(v0) + float(v1 - v0) * float(time_elapsed - time0) / float(time1 - time0)


def _calcurate_volume(time_elapsed, schedule):
    volume = 0
    if ('media' in config.config.keys()) and (len(config.config['media']['volume']) > 0):
        sch = config.convert_volume_schedule(schedule)
        for i, t in enumerate(sch):
            if time_elapsed >= t['time']:
                t2 = None
                if i == len(sch) - 1:
                    t2 = t
                else:
                    if time_elapsed < sch[i + 1]["time"]:
                        t2 = sch[i + 1]
                if t2:
                    volume = _calcurate_volume_sub(time_elapsed, t['time'], t2['time'], t['volume'], t2['volume'])
                    break
    return volume


def _is_elapsed_interval(time_elapsed, time_last, interval):
    if interval < 0:
        return False
    elif time_last < 0:
        return True
    if (time_elapsed - time_last) >= interval:
        return True
    elif interval >= 60:
        now = datetime.datetime.now()
        if now.second > 0 and now.second <= 30:
            return (time_elapsed + (60 - now.second - 1) - time_last) >= interval


def _is_elapsed_speak_interval(time_elapsed, time_last, schedule):
    interval = -1
    sch = config.convert_speech_schedule(schedule)
    for t in sch:
        if time_elapsed >= t['time']:
            interval = t['interval']
    return _is_elapsed_interval(time_elapsed, time_last, interval)


def _get_script_or_executable_dir():
    f = __file__
    if getattr(sys, "frozen", False):
        f = sys.executable
    return pathlib.Path(f).parent.resolve()


def _run():
    if config.config['media']['enable']:
        vlc.start_app()

    start_time = datetime.datetime.now()

    if config.config['master_volume'] >= 0:
        system_volume.SystemVolume().set_volume(config.config['master_volume'])

    if config.config['media']['enable']:
        vlc.set_volume(int(_calcurate_volume(0, config.config['media']['volume'])))

    if config.config['weather']['enable']:
        weather_api.set_api_key(config.config['weather']['apikey'])
        if (config.config['weather']['apikey'] == '0000000000000000000000000000000'):
            _logger.error("weather apikey(%s) in setting is not valid", config.config['weather']['apikey'])
        weather_data = _get_weather()

    duration = config.time_range_to_seconds(config.config['duration'])
    last_weather_update_time = 0
    last_weather__speak_time = -1
    last_time__speak_time = -1
    old_meta_title = None

    while True:
        if config.config['media']['enable']:
            if not vlc.find_app():
                _logger.info("vlc terminated")
                break

        time_elapsed = (datetime.datetime.now() - start_time).seconds
        if duration > 0 and time_elapsed >= duration:
            _logger.info("finish")
            if config.config['media']['enable']:
                vlc.kill_app()
            break

        if config.config['media']['enable']:
            status = vlc.get_status().json()
            try:
                if 'information' in status and status['information']['category']['meta']['title'] != old_meta_title:
                    _logger.info("title: %s / %s / %s", status['information']['category']['meta']['title'], str(datetime.timedelta(seconds=status['length'])), status['information']['category']['meta']['album'])
                    old_meta_title = status['information']['category']['meta']['title']
            except Exception as _:
                if config.config["debug"]:
                    _logger.exception("cannot get title")

            # start a new playlist
            if _select_current_playlist(time_elapsed) or status["state"] == "stopped":
                _logger.debug("start playlist")
                _start_current_playlist()

            # update media volume
            new_volume = int(_calcurate_volume(time_elapsed, config.config['media']['volume']))
            if int(status["volume"]) != new_volume:
                _logger.debug("vlc_volume:%d", new_volume)
                vlc.set_volume(new_volume)

        time_speech_flag = False
        weather_speech_flag = False

        # time speech
        if config.config['time']['enable']:
            if _is_elapsed_speak_interval(time_elapsed, last_time__speak_time, config.config['time']['interval']):
                time_speech_flag = True

        # weather speech
        if config.config['weather']['enable']:
            # update weather forecast
            if _is_elapsed_interval(time_elapsed, last_weather_update_time, config.time_range_to_seconds(config.config['weather']['update_interval'])):
                _logger.debug("updating weather data")
                weather_data = _get_weather()
                last_weather_update_time = time_elapsed
                _logger.debug("weather data updated")

            # weather forecast speaking
            if _is_elapsed_speak_interval(time_elapsed, last_weather__speak_time, config.config['weather']['interval']):
                weather_speech_flag = True
        
        if time_speech_flag or weather_speech_flag:
            _set_random_locale()
            _set_speech_voice()

            if time_speech_flag:
                new_volume = int(_calcurate_volume(time_elapsed, config.config['time']['volume']))
                _logger.debug("time_volume:%d", new_volume)
                _set_speech_volume(new_volume)
                _speech_time()
                last_time__speak_time = time_elapsed

            if weather_speech_flag:
                new_volume = int(_calcurate_volume(time_elapsed, config.config['weather']['volume']))
                _logger.debug("weather_volume:%d", new_volume)
                _set_speech_volume(new_volume)
                locale = i18n.config.get('locale')
                if weather_data[locale]:
                    _logger.debug("weather:%s", weather_data[locale])
                    _speech_text(weather_data[locale])
                last_weather__speak_time = time_elapsed

        time.sleep(5)


if __name__ == "__main__":
    script_directory = _get_script_or_executable_dir()
    default_config = os.path.abspath("config.json")
    if not os.path.exists(default_config):
        default_config = os.path.join(script_directory, "config.json")

    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument('--config', help='config file', default=default_config)
    args = parser.parse_args()

    config_path = os.path.abspath(args.config)
    _logger.info("config: %s", config_path)
    config.load(config_path)

    if config.config['debug']:
        log.setDebugLevel(__name__)
        vlc.set_debug_level()
        weather_api.set_debug_level()

        import json
        _logger.debug(json.dumps(config.config, ensure_ascii=False, indent=1))

    vlc.set_param(config.config["media"]["vlc"]["command"], config.config["media"]["vlc"]["http_host"], config.config["media"]["vlc"]["http_port"], config.config["media"]["vlc"]["http_password"])
    playlist.set_param(config.config['media']['extensions']['media'], config.config['media']['extensions']['playlist'])

    i18n.load_path.append(os.path.join(script_directory, "translations"))
    i18n.set("file_format", "json")
    i18n.set('locale', 'en')
    i18n.set('fallback', 'en')
    i18n.set("skip_locale_root_data", True)

    _run()
