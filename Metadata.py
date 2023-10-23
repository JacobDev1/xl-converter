import shutil, platform
from Process import Process
from VARIABLES import EXIFTOOL_PATH, EXIFTOOL_FOLDER_PATH, EXIFTOOL_BIN_NAME

class Metadata():
    def __init__(self):
        self.p = Process()

    def copyAttributes(self, src, dst):
        """Copy all attributes from one file onto another."""
        try:
            shutil.copystat(src, dst)
        except OSError as e:
            self.log(f"[Error] copystat failed ({e})")

    def _runExifTool(self, args):
        """For internal use only."""
        if platform.system() == "Windows":
            self.p.runProcess(f'\"{EXIFTOOL_PATH}\" {args}')
        elif platform.system() == "Linux":  # Relative path needed for Brotli dependency to work on Linux
            self.p.runProcessFromPath(f'./{EXIFTOOL_BIN_NAME} {args}', EXIFTOOL_FOLDER_PATH)

    def copyMetadata(self, src, dst):
        """Copy all metadata from one file onto another."""
        self._runExifTool(f'-tagsfromfile \"{src}\" -overwrite_original \"{dst}\"')

    def deleteMetadata(self, dst):
        """Delete all metadata except color profile from a file."""
        self._runExifTool(f'-all= -tagsfromfile @ -colorspacetags -overwrite_original \"{dst}\"')