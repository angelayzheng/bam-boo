from pathlib import Path

from challenges.audio import validate_audio_file
from challenges.use_cases.ports import AudioValidator


class FfprobeAudioValidator(AudioValidator):
    def validate(self, folder: Path, relative_path: str) -> None:
        validate_audio_file(folder / relative_path)
