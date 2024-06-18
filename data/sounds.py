from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

from data.constants import FINISHED_SOUND_PATH

class SoundPlayer:
    def __init__(self, audio_path, volume=0.5):
        self.sound = QSoundEffect()
        self.sound.setVolume(volume)
        self.audio_path = audio_path
    
    def play(self, volume=None):
        if not self.sound.isLoaded():
            self.sound.setSource(QUrl.fromLocalFile(self.audio_path))
        if volume is not None:
            self.sound.setVolume(volume)
        self.sound.play()

# Sound bank
finished_sound = SoundPlayer(FINISHED_SOUND_PATH)