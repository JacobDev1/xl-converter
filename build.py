import platform
import os
import shutil
import subprocess
import argparse
import stat
import hashlib
from pathlib import Path
import re
import glob
import plistlib
import tempfile
import errno

import PyInstaller.__main__
import requests

from data.constants import VERSION

PROGRAM_FOLDER = os.path.dirname(os.path.realpath(__file__))

def replaceLine(path, pattern, new_line):
    """Replace the first line containing a pattern."""
    path = os.path.normpath(path)
    if not os.path.isfile(path):
        return

    content = ""
    with open(path, "r") as file:
        content = file.readlines()
    
    for n, line in enumerate(content):
        if pattern in line:
            if line != new_line:    # If the file wouldn't be the same
                content[n] = new_line
                break   # Only one line needs to be replaced
            else:
                return
    
    with open(path, "w") as file:
        file.writelines(content)

def removeReadOnly(path: str) -> None:
    """Removes "Read-only" attribute from files and folders recursively. Windows-only."""
    if platform.system() != "Windows":
        raise Exception("[removeReadOnly] Wrong OS")

    for file_path in Path(path).rglob("*"):
        if file_path.is_file():
            try:
                file_path.chmod(stat.S_IWRITE)
            except Exception as e:
                raise OSError(f"[removeReadOnly] Failed to remove \"Read-only\" attribute. {e}")

def copy(src, dst):
    src = os.path.normpath(src)
    dst = os.path.normpath(dst)

    try:
        shutil.copy(src, dst)
    except OSError as err:
        print(f"[Error] Copying failed ({src} -> {dst}) ({err})")

def move(src, dst):
    src = os.path.normpath(src)
    dst = os.path.normpath(dst)

    try:
        shutil.move(src, dst)
    except OSError as err:
        print(f"[Error] Moving failed ({src} -> {dst}) ({err})")

def makedirs(path):
    path = os.path.normpath(path)

    try:
        os.makedirs(path, exist_ok=True)
    except OSError as err:
        print(f"[Error] Makedirs failed ({path}) ({err})")

def addExecPerm(path):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)

def rmTree(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

def blake2(path):
    """Calculate the blake2 hash."""
    hasher = hashlib.blake2b()

    with open(path, "rb") as file:
        buff_size = 8192
        for buf in iter(lambda: file.read(buff_size), b""):
            hasher.update(buf)
    
    return hasher.hexdigest()

class Downloader():
    """Downloads dependencies."""
    def __init__(self):
        self.appimagetool_url = "https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-x86_64.AppImage"
        self.appimagetool_dst = "misc/appimagetool"
        self.appimagetool_blake2 = "83db0c2644d992045f974592099fdbf69c690f20d8440e773bfb76fff199d4abf9a3b19a72279e63b9aa37ef46b201ced2a106138c0404e2a03de2f7b390c4a5"

    def download(self, url, dst, checksum = None):
        dst = Path(dst)
        if dst.is_file():
            return

        # Download the file
        print(f"[Downloading] Downloading {dst.name}")
        response = requests.get(url)
        if response.status_code == 200:
            with open(Path(dst), 'wb') as f:
                f.write(response.content)
        else:
            print(f"[Downloading] Downloading failed ({dst.name})")
            raise Exception(f"[Downloading] Status code: {response.status_code}")
        
        # Verify the checksum
        if checksum is not None:
            if blake2(dst) != checksum:
                raise Exception(f"[Downloading] Checksum mismatch ({dst.name})")
        
        # Permissions
        addExecPerm(dst)
        print(f"[Downloading] Download completed ({dst.name})")

    def downloadAppImageTool(self):
        self.download(self.appimagetool_url, self.appimagetool_dst, self.appimagetool_blake2)
    
class Args():
    def __init__(self):
        self.parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        self.args = {}
        self.parser.add_argument("--build-type", "-b",
                help="""Type of build to generate.
not specified: vanilla build on Windows and Linux. app bundle on macOS.
sh (Linux only): 7z archive with an installer script.
appimage (Linux only): an AppImage build.
innosetup (Windows only): an InnoSetup script and build ready to compile.
portable (Windows only): 7z archive with the program.
dmg (macOS only): app wrapped in a dmg archive.
""",
                action="store"
        )
        self.parser.add_argument("--update-file", "-u", help="Append an update file (to place on a server).", action="store_true")

        self._parseArgs()

    def _parseArgs(self):
        args = self.parser.parse_args()
        self.args["build_type"] = args.build_type
        self.args["update_file"] = args.update_file

    def getArg(self, arg):
        return self.args[arg]

class Builder():
    # You can use the "/" symbol to divide paths (the functions will normalize it)
    def __init__(self):
        self.args = Args()
        self.downloader = Downloader()

        # General
        self.project_name = "xl-converter" 
        self.project_display_name = "XL Converter"
        self.dst_dir = "dist"
        self.internal_dir = f"{self.dst_dir}/{self.project_name}/_internal"
        self.icon_svg_path = "assets/icons/logo.svg"

        # Shared
        self.bin_dir = {
            "Windows": "bin/win",
            "Linux": "bin/linux",
            "Darwin": "bin/macos",
        }

        self.installer_path = {
            "Windows": "misc/install.iss",
            "Linux": "misc/install.sh"
        }

        self.assets = (
            "LICENSE.txt",
            "LICENSE_3RD_PARTY.txt",
            "./fonts/",
            "./assets/",
        )

        # Assets
        self.fonts_path = "fonts"

        # Linux
        self.desktop_entry_path = "misc/xl-converter.desktop"
        self.version_file_path = "misc/version.json"
        self.appimagetool_path = "misc/appimagetool"

        # Windows
        self.win_7z_path = "C:\\Program Files\\7-Zip\\7z.exe"

        # macOS
        self.macos_app_bundle_name = "XL Converter.app"
        self.logo_icns_path = None
        self.macos_dmg_background = "misc/images/macos_dmg_background.svg"
        
        # Build Names
        self.version_sanitized = re.sub(r"[ \n]", "-", VERSION)   # No whitespaces or newline characters
        self.build_inno_name = f"xl-converter-win-{self.version_sanitized}-x86_64"
        self.build_win_portable_name = f"xl-converter-win-{self.version_sanitized}-x86_64-portable"
        
        self.build_7z_name = f"xl-converter-linux-{self.version_sanitized}-x86_64"
        self.build_appimage_name = f"xl-converter-linux-{self.version_sanitized}-x86_64.AppImage"

        self.build_macos_app_name = f"xl-converter-macos-{self.version_sanitized}-universal.app"
        self.build_macos_dmg_name = f"xl-converter-macos-{self.version_sanitized}-universal.dmg"

        # Clean up
        # base path: xl-converter/_internal
        self.cleanup_resources = {
            "Linux": [
                # "PySide6/QtNetwork*",     # QSoundEffect needs it.
                # "PySide6/Qt/lib/Qt6Network*",
                "PySide6/Qt/lib/libavcodec*",
                "PySide6/Qt/lib/libavformat*",
                "PySide6/Qt/lib/libavutil*",
                "PySide6/Qt/lib/libQt6OpenGL*",
                "PySide6/Qt/lib/libQt6Pdf*",
                "PySide6/Qt/lib/libQt6Qml*",
                "PySide6/Qt/lib/libQt6Quick*",
                "PySide6/Qt/lib/libswscale*",
                "PySide6/Qt/lib/libQt6VirtualKeyboard*",

                "PySide6/Qt/plugins/imageformats",
                "PySide6/Qt/plugins/multimedia",
                "PySide6/Qt/translations",
            ],
            "Windows": [
                "PySide6\\avcodec-61.dll",
                "PySide6\\avformat-61.dll",
                "PySide6\\avutil-59.dll",
                "PySide6\\opengl32sw.dll",
                # "PySide6\\Qt6Network.dll",
                "PySide6\\Qt6OpenGL.dll",
                "PySide6\\Qt6Pdf.dll",
                "PySide6\\Qt6Qml.dll",
                "PySide6\\Qt6QmlMeta.dll",
                "PySide6\\Qt6QmlModels.dll",
                "PySide6\\Qt6Quick.dll",
                "PySide6\\Qt6VirtualKeyboard.dll",
                "PySide6\\swresample-5.dll",
                "PySide6\\swscale-8.dll",

                "PySide6\\plugins\\imageformats",
                "PySide6\\Qt6MultimediaWidgets",
                "PySide6\\translations",
            ],
            "Darwin": [
                "PySide6/Qt/lib/libavcodec*",
                "PySide6/Qt/lib/libavformat*",
                "PySide6/Qt/lib/libavutil*",
                "PySide6/Qt/lib/QtOpenGL*",
                "PySide6/Qt/lib/QtPdf*",
                "PySide6/Qt/lib/QtQml*",
                "PySide6/Qt/lib/QtQuick*",
                "PySide6/Qt/lib/libswscale*",
                "PySide6/Qt/lib/QtVirtualKeyboard*",

                "PySide6/Qt/plugins/imageformats",
                "PySide6/Qt/plugins/multimedia",
                "PySide6/Qt/translations",
            ]
        }

    def build(self):
        build_type = self.args.getArg('build_type')

        if build_type is not None and build_type not in ("sh", "appimage", "appimage-skip-packing", "innosetup", "portable", "dmg"):
            raise Exception("build_type incorrect")

        self._prepare()
        if platform.system() == "Darwin":
            self.logo_icns_path = os.path.join(PROGRAM_FOLDER, "./misc/images", "logo.icns")
            self._generateMacIcnsIcon(
                os.path.join(PROGRAM_FOLDER, self.icon_svg_path),
                self.logo_icns_path,
            )
        self._buildBinaries()
        self._reduceBundleSize()
        self._copyDependencies()
        self._copyAssets()

        match platform.system():
            case "Linux":
                match build_type:
                    case "sh":
                        self._appendDesktopEntry()
                        self._appendInstaller()
                        self._build7z()
                    case "appimage" | "appimage-skip-packing":
                        self._appendDesktopEntry()
                        self._buildAppImage(skip_packing=build_type == "appimage-skip-packing")
            case "Windows":
                match build_type:
                    case "innosetup":
                        self._appendInstaller()
                    case "portable":
                        self._appendConfig(portable=True)
                        self._buildPortableWin()
            case "Darwin":
                rmTree(f"{self.dst_dir}/{self.project_name}")   # Remove leftover dist/xl-converter
                match build_type:
                    case "dmg":
                        self._buildDmg()
       
        if self.args.getArg("update_file"):
            self._appendUpdateFile()
        
        print(f"[Building] Finished (built to {self.dst_dir}/{self.project_name})")
        if platform.system() == "Darwin":
            print("[Warning] macOS build support is experimental. Some tools in ./bin/macos are not self-contained. This bundle will not work on another machine! Use for testing only.")

    def _prepare(self):
        if platform.system() == "Windows":
            # On Windows some ExifTool files may get a read-only attribute when unpacking from a 7z.
            removeReadOnly(self.dst_dir)
            # Remove read-only in ./bin/win as it can be problematic later on.
            removeReadOnly(self.bin_dir["Windows"])
        
        try:
            if os.path.isdir(self.dst_dir):
                shutil.rmtree(self.dst_dir)
        except OSError as e:
            if platform.system() == "Darwin" and e.errno == errno.ENOTEMPTY:
                print("Close or move Finder out of the ./dist directory, and try again.")
            raise
        
    def _buildBinaries(self):
        print("[Building] Generating binaries")
        makedirs(self.dst_dir)
        PyInstaller.__main__.run([
            "--log-level=ERROR",
            "--workpath=./_pyinstaller",
            str(Path("misc/main.spec"))
        ])
    
    def _copyDependencies(self):
        print("[Building] Copying dependencies")
        bin_dir = self.bin_dir[platform.system()]
        shutil.copytree(Path(bin_dir), Path(self.internal_dir, bin_dir))
    
    def _appendInstaller(self):
        installer_dir = self.installer_path[platform.system()]
        installer_file = os.path.basename(installer_dir)

        print("[Building] Appending an installer script")
        match platform.system():
            case "Linux":
                copy(installer_dir, self.dst_dir)
                print("[Building] Embedding version into an installer script")
                replaceLine(f"{self.dst_dir}/{installer_file}", "VERSION=", f"VERSION=\"{VERSION}\"\n")
            case "Windows":
                copy(installer_dir, self.dst_dir)
                print("[Building] Embedding version into an installer script")
                replaceLine(f"{self.dst_dir}/{installer_file}", "#define MyAppVersion", f"#define MyAppVersion \"{VERSION}\"\n")
                replaceLine(f"{self.dst_dir}/{installer_file}", "OutputBaseFilename=", f"OutputBaseFilename={self.build_inno_name}\n")
    
    def _appendDesktopEntry(self):
        if platform.system() == "Linux":
            print("[Building] Appending a desktop entry")
            copy(self.desktop_entry_path, self.dst_dir)
    
    def _copyAssets(self):
        print("[Building] Appending assets")
        
        if platform.system() == "Darwin":
            dst = os.path.join(self.dst_dir, self.macos_app_bundle_name, "Contents", "Frameworks")
        else:
            dst = self.internal_dir

        for i in self.assets:
            if os.path.isdir(Path(i)):
                shutil.copytree(Path(i), Path(dst, Path(i).name))
            elif os.path.isfile(Path(i)):
                copy(i, dst)

    def _appendUpdateFile(self):
        print("[Building] Appending an update file (to place on a server)")
        copy(self.version_file_path, self.dst_dir)
        replaceLine(f"{self.dst_dir}/{os.path.basename(self.version_file_path)}", "latest_version", f"    \"latest_version\": \"{VERSION}\",\n")

    def _appendConfig(self, portable=True):
        config = "[General]\n"

        if portable:    config += "portable_user_data = True\n"

        with open(Path(self.internal_dir, "config.ini"), "w") as f:
            f.write(config)

    # _build methods transform the directory!
    def _buildAppImage(self, skip_packing=False):
        if platform.system() != "Linux":
            return

        self.downloader.downloadAppImageTool()

        print("[Building] Building an AppImage")
        dsk_ent_f = os.path.basename(self.desktop_entry_path)
        dsk_ent_p = f"{self.dst_dir}/{dsk_ent_f}"
        appdir = f"{self.dst_dir}/AppDir"

        replaceLine(dsk_ent_p, "Icon=", "Icon=/logo\n")
        replaceLine(dsk_ent_p, "Exec=", "Exec=/AppRun\n")
        
        makedirs(f"{appdir}/usr/bin")
        move(dsk_ent_p, f"{appdir}/{dsk_ent_f}")
        with open(f"{appdir}/AppRun", "w") as f:
            f.write("#!/bin/bash\n\n")
            f.write(f"exec ${{APPDIR}}/usr/bin/{self.project_name}/{self.project_name} $@")
        addExecPerm(f"{appdir}/AppRun")

        # Add Icon
        copy(f"./assets/icons/logo.svg", appdir)

        # Build
        move(f"{self.dst_dir}/{self.project_name}", f"{appdir}/usr/bin")    # Move the whole project folder
        
        if skip_packing:
            with open(f"{self.dst_dir}/build_name.txt", "w") as file:
                file.write(self.build_appimage_name)
        else:
            subprocess.run((self.appimagetool_path, appdir, f"{self.dst_dir}/{self.build_appimage_name}"))

    def _build7z(self):
        if platform.system() != "Linux":
            return

        dst_direct = self.build_7z_name
        dst = f"{self.dst_dir}/{self.build_7z_name}"
        makedirs(dst)

        move(f"{self.dst_dir}/{self.project_name}", dst)
        move(f"{self.dst_dir}/{os.path.basename(self.installer_path['Linux'])}", dst)
        move(f"{self.dst_dir}/{os.path.basename(self.desktop_entry_path)}", dst)
        subprocess.run(("7z", "a", "-snl" , f"{dst_direct}.7z", dst_direct), cwd=self.dst_dir)
    
    def _buildPortableWin(self) -> None:
        # Scan for available 7zip installs
        def is7zipWorking(path: str) -> bool:
            try:
                result = subprocess.run(
                    [path, "--help"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                return "Add files to archive" in result.stdout
            except Exception:
                return False

        win_7z_path_used = None

        if os.path.isfile(self.win_7z_path) and is7zipWorking(self.win_7z_path):
            win_7z_path_used = self.win_7z_path
        elif is7zipWorking("7z"):
            win_7z_path_used = "7z"
        
        if win_7z_path_used is None:
            raise Exception("Install 7zip to continue.")

        # Pack
        try:
            shutil.move(
                os.path.join(self.dst_dir, self.project_name),
                os.path.join(self.dst_dir, self.build_win_portable_name)
            )
        except OSError as e:
            raise OSError(f"Failed to move file (_buildPortableWin) {e}")
        subprocess.run([
            win_7z_path_used,
            "a",
            f"{self.build_win_portable_name}.7z",
            self.build_win_portable_name,
        ], cwd=self.dst_dir)

    def _generateMacIcnsIcon(self, svg_src: str, icns_dst: str) -> None:
        if platform.system() != "Darwin":
            return

        with tempfile.TemporaryDirectory(prefix="xl_converter_icon_") as iconset_dir:
            png_src = os.path.join(iconset_dir, "icon.png")
            subprocess.run(
                ["rsvg-convert", "-w", "2048", svg_src, "-o", png_src],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            iconset_dir = os.path.join(iconset_dir, "bundle.iconset")
            makedirs(iconset_dir)
            sizes = [
                16, 32, 64, 128, 256, 512
            ]
            for size in sizes:
                for retina in (True, False):
                    pixels = size * (2 if retina else 1)
                    suffix = "@2x" if retina else ""
                    name = f"icon_{size}x{size}{suffix}.png"
                    output_path = os.path.join(iconset_dir, name)
                    subprocess.run(
                        ["sips", "-z", str(pixels), str(pixels), png_src, "--out", output_path],
                        check=True,
                        stdout=subprocess.DEVNULL,
                    )

            if os.path.exists(icns_dst):
                os.remove(icns_dst)
            makedirs(os.path.dirname(os.path.normpath(icns_dst)))
            subprocess.run(
                ["iconutil", "-c", "icns", iconset_dir, "-o", icns_dst],
                check=True,
                stdout=subprocess.DEVNULL,
            )

    def _buildDmg(self) -> None:
        if platform.system() != "Darwin":
            return

        print("[Building] Creating dmg archive")

        try:
            import dmgbuild
        except ImportError:
            raise

        app_dir = os.path.join(self.dst_dir, self.macos_app_bundle_name)
        dmg_output = os.path.join(self.dst_dir, self.build_macos_dmg_name)
        license_path = os.path.join(PROGRAM_FOLDER, "LICENSE.txt")

        with tempfile.TemporaryDirectory(prefix="xl_converter_dmg_", dir=self.dst_dir) as tmp_dir:
            dmg_background_path = os.path.join(tmp_dir, "dmg_background.png")
            dmg_settings_path = os.path.join(tmp_dir, "dmg_settings.py")
            dmg_settings_py = f"""
format = "ULMO"

files = [
    f"{app_dir}",
    (f"{license_path}", "LICENSE.txt"),
]
hide = [
    "LICENSE.txt",
]
symlinks = {{ "Applications": "/Applications" }}
license = {{
    "default-language": "en_US",
    "licenses": {{
        "en_US": r"{license_path}",
    }},
}}

icon_locations = {{
    f"{self.macos_app_bundle_name}": (140, 150),
    "Applications": (500, 150),
}}
# NOTE: Font color always remains black if a background is set. Finder doesn't adjust the font color here.
background = f"{dmg_background_path}"
badge_icon = f"{self.logo_icns_path}"
window_rect = ((100, 100), (640, 360))
default_view = "icon-view"
icon_size = 128
text_size = 14
"""
            subprocess.run(
                ["rsvg-convert", "-w", "640", "-h", "360", self.macos_dmg_background, "-o", dmg_background_path],
                check=True,
            )

            with open(dmg_settings_path, "w", encoding="utf-8") as f:
                f.write(dmg_settings_py)
            
            try:
                subprocess.run([
                    "dmgbuild", "-s", dmg_settings_path, self.project_display_name, dmg_output,
                ], check=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"dmgbuild failed: {e}") from e

    def _reduceBundleSize(self) -> None:
        print("[Building] Reducing bundle size")

        current_system = platform.system()
        if current_system not in self.cleanup_resources:
            raise Exception(f"_reduceBundleSize is unsupported for {current_system}")
        
        if current_system == "Darwin":
            contents_dir = os.path.join(self.dst_dir, self.macos_app_bundle_name, "Contents")
            roots = [
                os.path.join(contents_dir, "Frameworks"),
                os.path.join(contents_dir, "Resources"),
            ]
        else:
            roots = [self.internal_dir]
    
        file_patterns = []
        for res in self.cleanup_resources[current_system]:
            for root in roots:
                file_patterns.append(os.path.join(root, res))
                if current_system == "Darwin":
                    file_patterns.append(os.path.join(root, os.path.basename(res)))

        files_to_remove = []
        for pattern in file_patterns:
            files_to_remove.extend(glob.glob(pattern))
        
        for path in files_to_remove:
            if not os.path.lexists(path):
                continue
            if os.path.islink(path):
                os.unlink(path)
            elif os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

if __name__ == '__main__':
    try:
        builder = Builder()
        builder.build()
    except (KeyboardInterrupt):
        print("[Canceled] Interrupted")
        exit()
    except SystemExit:
        exit()
    except (Exception, OSError) as err:
        print(f"[Error] {err}")
        exit()
