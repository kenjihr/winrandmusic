import glob
import os
import random

_config = {
    "extensions": {
        "media": ["wav", "mp3", "flac", "alac", "aac", "ogg", "wma", "m4a", "mp4"],
        "playlist": ["m3u8", "m3u"]
    }
}


def _is_file_with_extension(path, extension_list):
    extention = os.path.splitext(path)[1]
    if extention and (extention[1:].lower() in extension_list):
        return True
    return False


def _is_playlist_file(path):
    return _is_file_with_extension(path, _config['extensions']['playlist'])


def _is_media_file(path):
    return _is_file_with_extension(path, _config['extensions']['media'])


def _is_media_directory(base_path):
    files = glob.glob(os.path.join(base_path, "**\\*.*"), recursive=True)
    for f in files:
        if _is_file_with_extension(f, _config['extensions']['media']):
            return True
    return False


def _find_sub_media_directories(base_dir):
    dirs = glob.glob(os.path.join(base_dir, "**\\"), recursive=True)
    for i in reversed(range(len(dirs))):
        if not _is_media_directory(dirs[i]):
            dirs.remove(dirs[i])
    return dirs


def _find_playlist_files(base_dir):
    files = glob.glob(os.path.join(base_dir, "**\\*.*"), recursive=True)
    for i in reversed(range(len(files))):
        if not _is_playlist_file(files[i]):
            files.remove(files[i])
    return files


def set_param(media_extensions=None, playlist_extensions=None):
    global _config
    if media_extensions is not None:
        _config['extensions']['media'] = media_extensions
    if playlist_extensions is not None:
        _config['extensions']['playlist'] = playlist_extensions


def get_playlists(base_playlists):
    playlists = []
    for playlist in base_playlists:
        playlist = os.path.expandvars(playlist)
        if os.path.exists(playlist):
            if os.path.isdir(playlist):
                dirs = _find_sub_media_directories(playlist)
                playlists += dirs

                files = _find_playlist_files(playlist)
                playlists += files
            else:
                if _is_playlist_file(playlist) or _is_media_file(playlist):
                    playlists.append(playlist)

    return sorted(list(set(playlists)))


def select_random_playlist(base_playlists):
    playlists = get_playlists(base_playlists)
    if len(playlists) > 0:
        index = random.randint(0, len(playlists) - 1)
        return playlists[index]
