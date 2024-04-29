import json
import os
import sys
import copy

config = \
{
    "locales": ["en"],                 # locales (en/ja) for speech
    "duration": "01:00:00",            # duration (hh:mm:ss). if time elapsed to the duration, app ends unless the duration is set to 00:00:00
    "master_volume": 0.8,              # system master volume (0.0-1.0, no change if negative)
    "media": {
        "enable": 1,                   # enable media play (0:disable 1:enable)
        "playlist": [                  # playlist
            {"time": "00:00:00", "playlist" : ["${USERPROFILE}\\Music\\classical"]},                        # at the beginning, use a playlist
            {"time": "01:00:00", "playlist" : ["${USERPROFILE}\\Music\\rock", "${PUBLIC}\\Music\\anime"]}   # after an hour, use another playlists
        ],
        "volume" : [                   # volume (0-300)
            {"time": "00:00:00", "volume": 0},      # at the beggining, volume is 0, then guradually changes to 60
            {"time": "00:30:00", "volume": 60},     # after 30 minites from the beggining, volume is 60, then guradually changes to 200
            {"time": "01:00:00", "volume": 200}     # after an hour from the beggining, volume is 200
        ],
        "vlc": {
            "command": ["C:\\Program Files\\VideoLAN\\VLC\\vlc.exe", "--random"],   # command for vlc
            "http_host": "127.0.0.1",      # host address for vlc's web interface
            "http_port": 28080,            # port number for vlc's web interface
            "http_password": "12345",      # password for vlc's web interface
        },
        "extensions": {
            "media": ["wav", "mp3", "flac", "alac", "aac", "ogg", "wma", "m4a", "mp4"], # extensions for media
            "playlist": ["m3u8", "m3u"]                                                 # extensions for playlist
        }
    },
    "time": {
        "enable": 1,                   # enable time speech (0:disable 1:enable)
        "interval": [                  # interval (hh:mm:ss) for each time
            {"time": "00:00:00", "interval": "00:10:00"},   # at the beggining, speeches the current time once in 10 minutes
            {"time": "00:30:00", "interval": "00:05:00"},   # after 30 minites from the beggining, speeches the current time once in 5 minutes
            {"time": "01:00:00", "interval": "00:01:00"}    # after an hour from the beggining, speeches the current time once in 1 minute
        ],
        "volume" : [                   # volume (0-100) for each time
            {"time": "00:00:00", "volume": 0},     # at the beggining, volume is 0, then guradually changes to 30
            {"time": "00:30:00", "volume": 30},    # after 30 minites from the beggining, volume is 30, then guradually changes to 100
            {"time": "01:00:00", "volume": 100}    # after an hour from the beggining, volume is 100
        ]
    },
    "weather": {
        "enable": 1,                   # enable weather speech (0:disable 1:enable)
        "interval": [                  # interval (hh:mm:ss) for each time
            {"time": "00:00:00", "interval": "00:10:00"},   # at the beggining, speeches today's weather once in 10 minutes
            {"time": "00:30:00", "interval": "00:05:00"},   # after 30 minites from the beggining, speeches today's weather once in 5 minutes
            {"time": "01:00:00", "interval": "00:01:00"}    # after an hour from the beggining, speeches today's weather once in 1 minute
        ],
        "volume" : [                   # volume (0-100) for each time
            {"time": "00:00:00", "volume": 0},     # at the beggining, volume is 0, then guradually changes to 30
            {"time": "00:30:00", "volume": 30},    # after 30 minites from the beggining, volume is 30, then guradually changes to 100
            {"time": "01:00:00", "volume": 100}    # after an hour from the beggining, volume is 100
        ],
        "update_interval": "01:00:00",                 # weather data update interval (hh:mm:ss)
        "q": "21.3058578441699,-157.85963020292868",   # latitude/longitude
        "apikey": "0000000000000000000000000000000"    # api key for weatherapi.com
    },
    "debug": 0
}


def _overwrite_values(d0, d1, keys):
    for i, key in enumerate(keys):
        if not key in d1:
            return
        if i == len(keys) - 1:
            d0[key] = d1[key]
        else:
            d0 = d0[key]
            d1 = d1[key]


def _get_keys(c):
    keys = []
    for k in c.keys():
        if isinstance(c[k], dict):
            keys2 = _get_keys(c[k])
            for k2 in keys2:
                keys.append([k] + k2)
        else:
            keys.append([k])
    return keys


def time_range_to_seconds(time_range_str):
    a = time_range_str.split(':')
    if len(a) == 3:
        return int(a[0]) * 60 * 60 + int(a[1]) * 60 + int(a[2])
    elif len(a) == 2:
        return int(a[1]) * 60 + int(a[2])
    return 0


def convert_volume_schedule(volume_schedule):
    schedule = copy.deepcopy(volume_schedule)
    for t in schedule:
        t['time'] = time_range_to_seconds(t['time'])
    return schedule


def convert_speech_schedule(speak_schedule):
    schedule = copy.deepcopy(speak_schedule)
    for t in schedule:
        t['time'] = time_range_to_seconds(t['time'])
        t['interval'] = time_range_to_seconds(t['interval'])
    return schedule


def convert_playlist_schedule(volume_schedule):
    schedule = copy.deepcopy(volume_schedule)
    for t in schedule:
        t['time'] = time_range_to_seconds(t['time'])
    return schedule


def load(config_file):
    global config
    if not os.path.exists(config_file):
        print(f"{config_file} not found.", file=sys.stderr)
        return

    with open(config_file, encoding='utf-8') as f:
        c = json.load(f)
        keys = _get_keys(config)
        for k in keys:
            _overwrite_values(config, c, k)
