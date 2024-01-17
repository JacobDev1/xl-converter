import platform
import os
import shutil
import subprocess
import argparse
import stat
from pathlib import Path

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

def copyTree(src, dst):
    src = os.path.normpath(src)
    dst = os.path.normpath(dst)

    try:
        shutil.copytree(src, dst, dirs_exist_ok=True)
    except OSError as err:
        print(f"[Error] Copying tree failed ({src} -> {dst}) ({err})")

def makedirs(path):
    path = os.path.normpath(path)

    try:
        os.makedirs(path)
    except OSError as err:
        print(f"[Error] Makedirs failed ({path}) ({err})")

def addExecPerm(path):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)

def rmTree(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

class Downloader():
    """Downloads dependencies."""
    def __init__(self):
        self.appimagetool_url = "https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-x86_64.AppImage"
        self.appimagetool_dst = "misc/appimagetool"

        self.redist_url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
        self.redist_dst = "misc/VC_redist.x64.exe"

    def download(self, url, dst):
        if Path(dst).is_file():
            return

        print(f"[Downloading] Downloading \"{dst}\"")        
        response = requests.get(url)
        if response.status_code == 200:
            with open(Path(dst), 'wb') as f:
                f.write(response.content)
        else:
            print(f"[Downloading] Downloading failed ({dst})")
        
        addExecPerm(dst)

    def downloadAppImageTool(self):
        self.download(self.appimagetool_url, self.appimagetool_dst)
    
    def downloadRedistributable(self):
        self.download(self.redist_url, self.redist_dst)

class Args():
    def __init__(self):
        self.parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        self.args = {}
        self.parser.add_argument("--app-image", "-a", help="package as an AppImage (Linux only)", action="store_true")
        self.parser.add_argument("--pack", "-p", help="package to a 7z (Linux only)", action="store_true")

        self._parseArgs()

    def _parseArgs(self):
        args = self.parser.parse_args()
        self.args["app_image"] = args.app_image
        self.args["pack"] = False if args.app_image else args.pack

        if platform.system() != "Linux":
            args_app_image = False
            args_pack = False
    
    def getArg(self, arg):
        return self.args[arg]

class Builder():
    # You can use the "/" symbol to divide paths (the functions will normalize it)
    def __init__(self):
        self.args = Args()
        self.downloader = Downloader()

        # General
        self.project_name = "xl-converter" 
        self.dst_dir = "dist"
        self.internal_dir = f"{self.dst_dir}/{self.project_name}/_internal"

        # Shared
        self.bin_dir = {
            "Windows": "bin/win",
            "Linux": "bin/linux"
        }

        self.installer_path = {
            "Windows": "misc/install.iss",
            "Linux": "misc/install.sh"
        }

        self.misc_path = (
            "LICENSE.txt",
            "LICENSE_3RD_PARTY.txt"
        )

        self.icon_svg_path = "icons/logo.svg"

        # Linux
        self.desktop_entry_path = "misc/xl-converter.desktop"
        self.version_file_path = "misc/version.json"
        self.appimagetool_path = "misc/appimagetool"

        # Windows
        self.redist_path = "misc/VC_redist.x64.exe"     # Needed for ImageMagick to work
        
        # Build Names
        self.build_inno_name = f"xl-converter-win-{VERSION}-x86_64"
        self.build_7z_name = f"xl-converter-linux-{VERSION}-x86_64"
        self.build_appimage_name = f"xl-converter-linux-{VERSION}-x86_64.AppImage"
    
    def build(self):
        self._prepare()
        self._buildBinaries()
        self._copyDependencies()
        self._appendInstaller()
        self._appendDesktopEntry()
        self._appendMisc()
        self._appendRedistributable()
        self._appendUpdateFile()
        self._finish()

        if self.args.getArg("app_image"):
            self._buildAppImage()
        elif self.args.getArg("pack"):
            self._build7z()

    def _prepare(self):
        rmTree(self.dst_dir)

        # Prevent conflicts If the same folder is used on multiple systems
        if os.path.isdir("build"):  
            if os.path.isfile("build/last_built_on"):
                last_built_on = open("build/last_built_on","r")
                last_platform = last_built_on.read()
                last_built_on.close()
                
                if last_platform == f"{platform.system()}_{platform.architecture()}":
                    print("[Building] Platform matches with previously compiled cache")
                else:
                    print("[Building] Platform mismatch - deleting the cache")
                    rmTree("build") 
                    rmTree("__pycache__")
            else:
                print("[Building] \"last_built_on\" not found - deleting the cache")
                rmTree("build")
                rmTree("__pycache__")
        
    def _buildBinaries(self):
        print("[Building] Generating binaries")
        makedirs(self.dst_dir)
        PyInstaller.__main__.run([
            str(Path("misc/main.spec"))
        ])
    
    def _copyDependencies(self):
        print("[Building] Copying dependencies")
        bin_dir = self.bin_dir[platform.system()]
        copyTree(bin_dir, f"{self.internal_dir}/{bin_dir}")
    
    def _appendInstaller(self):
        installer_dir = self.installer_path[platform.system()]
        installer_file = os.path.basename(installer_dir)

        match platform.system():
            case "Linux":
                if self.args.getArg("app_image") == False:
                    print("[Building] Appending an installer script")
                    copy(installer_dir, self.dst_dir)
                    if self.args.getArg("app_image") == False:
                        print("[Building] Embedding version into an installer script")
                        replaceLine(f"{self.dst_dir}/{installer_file}", "VERSION=", f"VERSION=\"{VERSION}\"\n")
            case "Windows":
                print("[Building] Appending an installer script")
                copy(installer_dir, self.dst_dir)
                print("[Building] Embedding version into an installer script")
                replaceLine(f"{self.dst_dir}/{installer_file}", "#define MyAppVersion", f"#define MyAppVersion \"{VERSION}\"\n")
                replaceLine(f"{self.dst_dir}/{installer_file}", "OutputBaseFilename=", f"OutputBaseFilename={self.build_inno_name}\n")
    
    def _appendDesktopEntry(self):
        if platform.system() == "Linux":
            print("[Building] Appending a desktop entry")
            copy(self.desktop_entry_path, self.dst_dir)
    
    def _appendMisc(self):
        print("[Building] Appending an icon and license files")
        for i in self.misc_path:
            copy(i, self.internal_dir)
        makedirs(f"{self.internal_dir}/icons")
        copy(self.icon_svg_path, f"{self.internal_dir}/icons/{os.path.basename(self.icon_svg_path)}")

    def _appendRedistributable(self):
        if platform.system() != "Windows":
            return

        self.downloader.downloadRedistributable()
        print("[Building] Appending redistributable")
        redist_dst = f"{self.dst_dir}/{self.project_name}/redist"
        makedirs(redist_dst)
        copy(self.redist_path, redist_dst)
    
    def _appendUpdateFile(self):
        print("[Building] Appending an update file (to place on a server)")
        copy(self.version_file_path, self.dst_dir)
        replaceLine(f"{self.dst_dir}/{os.path.basename(self.version_file_path)}", "latest_version", f"    \"latest_version\": \"{VERSION}\",\n")
    
    def _finish(self):
        with open("build/last_built_on","w") as last_built_on:
            last_built_on.write(f"{platform.system()}_{platform.architecture()}")

        print(f"[Building] Finished (built to {self.dst_dir}/{self.project_name})")

    # _build methods transform the directory!
    def _buildAppImage(self):
        if platform.system() != "Linux":
            return

        self.downloader.downloadAppImageTool()

        print("[Building] Building an AppImage")
        dsk_ent_f = os.path.basename(self.desktop_entry_path)
        dsk_ent_p = f"{self.dst_dir}/{dsk_ent_f}"
        appdir = f"{self.dst_dir}/AppDir"

        replaceLine(dsk_ent_p, "Icon=", "Icon=/logo\n")
        replaceLine(dsk_ent_p, "Path=", "")
        replaceLine(dsk_ent_p, "Exec=", "Exec=AppRun\n")
        
        makedirs(f"{appdir}/usr/bin")
        copy(self.icon_svg_path, appdir)
        move(dsk_ent_p, f"{appdir}/{dsk_ent_f}")
        with open(f"{appdir}/AppRun", "w") as f:
            f.write("#!/bin/bash\n\n")
            f.write(f"exec ${{APPDIR}}/usr/bin/{self.project_name}/{self.project_name} $@")
        addExecPerm(f"{appdir}/AppRun")

        move(f"{self.dst_dir}/{self.project_name}", f"{appdir}/usr/bin")    # Move the whole project folder
        subprocess.run((self.appimagetool_path, appdir, f"{self.dst_dir}/{self.build_appimage_name}"))

    def _build7z(self):
        dst_direct = self.build_7z_name
        dst = f"{self.dst_dir}/{self.build_7z_name}"
        makedirs(dst)

        move(f"{self.dst_dir}/{self.project_name}", dst)
        move(f"{self.dst_dir}/{os.path.basename(self.installer_path['Linux'])}", dst)
        move(f"{self.dst_dir}/{os.path.basename(self.desktop_entry_path)}", dst)
        subprocess.run(("7z", "a", f"{dst_direct}.7z", dst_direct), cwd=self.dst_dir)


if __name__ == '__main__':
    try:
        builder = Builder()
        builder.build()
    except (KeyboardInterrupt, SystemExit):
        print("[Building] Interrupted")
        exit()
    except (Exception, OSError) as err:
        print(f"[Building] Error - ({err})")
        exit()