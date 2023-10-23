import shutil, platform
from Process import Process
from VARIABLES import (
    EXIFTOOL_PATH, EXIFTOOL_FOLDER_PATH, EXIFTOOL_BIN_NAME,
    IMAGE_MAGICK_PATH,
    CJXL_PATH,
    AVIFENC_PATH,
    OXIPNG_PATH
)

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
        self._runExifTool(f'-all= --icc_profile:all -tagsFromFile @ -ColorSpace -overwrite_original \"{dst}\"')
    
    def deleteMetadataUnsafe(self, dst):
        """Deletes every last bit of metadata, even color profile. May mess up an image. Potentially desctructive."""
        self._runExifTool(f'-all= -overwrite_original \"{dst}\"')

    def runExifTool(self, src, dst, mode):
        match mode:
            case "ExifTool - Safe Wipe":
                self.deleteMetadata(dst)
            case "ExifTool - Preserve":
                self.copyMetadata(src, dst)
            case "ExifTool - Unsafe Wipe":
                self.deleteMetadataUnsafe(dst)
    
    def getArgs(self, encoder, mode):
        """Get metadata specific arguments for chosen encoder.

        Usage:
            args.extend(getArgs(encoder, mode))
        """
        match mode:
            case "Up to Encoder - Wipe":
                # No Switch case, because it would require a Class in this situation
                if encoder == CJXL_PATH:
                    return []
                    # The following has no effect on the encoder.
                    # return ["-x strip=exif", "-x strip=xmp", "-x strip=jumbf"]    
                    # return ["-x exif=", "-x xmp=", "-x jumbf="]
                    # The source code for reference https://github.com/libjxl/libjxl/blob/6f85806063394d0f32e6a112a37a259214bed4f1/tools/cjxl_main.cc
                elif encoder == IMAGE_MAGICK_PATH:
                    return ["-strip"]
                elif encoder == AVIFENC_PATH:
                    return  ["--ignore-exif", "--ignore-xmp"]
                elif encoder == OXIPNG_PATH:
                    return ["--strip safe"]
                else:
                    print(f"[Metadata - getArgs()] Unrecognized encoder ({encoder})")
            case "Up to Encoder - Preserve":
                return []   # Encoders preserve metadata by default
            case _:     # Necessary
                return []