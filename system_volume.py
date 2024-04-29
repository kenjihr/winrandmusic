from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class SystemVolume:
    def __init__(self):
        self.devices = AudioUtilities.GetSpeakers()
        self.interface = self.devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = self.interface.QueryInterface(IAudioEndpointVolume)

    # オーディオデバイスのマスターボリュームレベルを取得。ボリュームレベルは、0.0 から 1.0 の範囲の正規化されたオーディオテーパ値
    def get_volume(self):
        return self.volume.GetMasterVolumeLevelScalar()

    # オーディオデバイスのマスターボリュームレベルを設定。ボリュームレベルは、0.0 から 1.0 の範囲の正規化されたオーディオテーパ値
    def set_volume(self, volume):
        self.volume.SetMasterVolumeLevelScalar(volume, None)

    # オーディオデバイスのミュート状態を取得
    # ミュート状態ならTrue、それ以外はFalseを返す
    def get_mute(self):
        muteValue = self.volume.GetMute()
        return muteValue != 0

    # オーディオデバイスのミュート状態を設定
    def set_mute(self, mute=True):
        muteValue = 0
        if mute:
            muteValue = 1
        self.volume.SetMute(muteValue, None)

    def __del__(self):
        self.volume.Release()
        self.interface.Release()
        self.devices.Release()
