import random
import win32com.client

_spvoice = win32com.client.Dispatch("SAPI.SpVoice")
_token_category = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
_token_category.SetID(r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices", False)


def _enumerate_voices():
    voices = []

    v = _spvoice.GetVoices()
    for i in range(v.Count):
        voices.append(v.Item(i))

    v = _token_category.EnumerateTokens()
    for i in range(v.Count):
        voices.append(v.Item(i))

    return voices


def _match_voice(voice, language, name):
    if language is not None and language != str(voice.GetAttribute("Language")):
        return False
    elif name is not None and name not in str(voice.GetAttribute("Name")):
        return False
    return True


def _get_voices(language=None, name=None):
    all_voices = _enumerate_voices()
    voices = []
    for v in all_voices:
        if _match_voice(v, language, name):
            voices.append(v)
    return voices


def get_voices(language=None, name=None):
    voices = _get_voices(language, name)
    for i, item in enumerate(voices):
        voices[i] = {
            "language": str(item.GetAttribute("Language")),
            "name": str(item.GetAttribute("Name"))
        }
    return voices


def set_voice(language=None, name=None):
    global _spvoice
    voices = _get_voices(language, name)
    for i in reversed(range(len(voices))):
        if not _match_voice(voices[i], language, name):
            voices.remove(voices[i])
    if len(voices) > 0:
        index = random.randint(0, len(voices) - 1)
        _spvoice.Voice = voices[index]


def set_volume(volume=100):
    global _spvoice
    _spvoice.Volume = volume


def speak(text):
    _spvoice.Speak(text)
