# Multiplatform makefile replacement
# I got fed up with trying to get `make` to work on Windows

import platform, os, shutil, glob, subprocess, PyInstaller.__main__, argparse, shutil, stat
from VARIABLES import VERSION

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

if __name__ == '__main__':
    args = Args()

    # Clean-up
    rmTree("dist")

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

    # Preapre Directory and Build Binaries
    print("[Building] Generating binaries")
    makedirs("dist")
    PyInstaller.__main__.run([
        'main.spec'
    ])

    # Copy Dependencies
    print("[Building] Copying dependencies")
    if platform.system() == "Windows":
        copyTree("bin/win/", f"dist/xl-converter/_internal/bin/win")
    elif platform.system() == "Linux":
        copyTree("bin/linux/", f"dist/xl-converter/_internal/bin/linux")

    # Append an Installer
    if platform.system() == "Linux":
        if args.getArg("app_image") == False:
            print("[Building] Appending an installer script")
            copy("misc/install.sh","dist")
        print("[Building] Appending a desktop entry")
        copy("misc/xl-converter.desktop","dist")
    elif platform.system() == "Windows":
        print("[Building] Appending an installer script")
        copy("misc/install.iss","dist")

    # Embed Version into an Installer
    if platform.system() == "Linux" and args.getArg("app_image") == False:
        print("[Building] Embedding version into an installer script")
        replaceLine(f"dist/install.sh", "VERSION=", f"VERSION=\"{VERSION}\"\n")
    elif platform.system() == "Windows":
        print("[Building] Embedding version into an installer script")
        replaceLine(f"dist/install.iss", "#define MyAppVersion", f"#define MyAppVersion \"{VERSION}\"\n")
        replaceLine(f"dist/install.iss", "OutputBaseFilename=", f"OutputBaseFilename=xl-converter-win-{VERSION}-x86_64\n")

    # Append misc.
    print("[Building] Appending an icon and license files")
    copy("LICENSE.txt", "dist/xl-converter/_internal")
    copy("LICENSE_3RD_PARTY.txt", "dist/xl-converter/_internal")
    makedirs(f"dist/xl-converter/_internal/icons")
    copy("icons/logo.svg", f"dist/xl-converter/_internal/icons/logo.svg")

    # Append an update file
    print("[Building] Appending an update file (to place on a server)")
    copy("misc/version.json", "dist")
    replaceLine("dist/version.json", "latest_version", f"    \"latest_version\": \"{VERSION}\",\n")

    # Append redistributables
    if platform.system() == "Windows":
        print("[Building] Appending redistributables")
        makedirs(f"dist/xl-converter/redistributables")
        copy("misc/VC_redist.x64.exe", f"dist/xl-converter/redistributables")
        # Needed for ImageMagick
        # https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170

    # Build AppImage
    if args.getArg("app_image"):
        replaceLine("dist/xl-converter.desktop", "Icon=", "Icon=/logo\n")
        replaceLine("dist/xl-converter.desktop", "Path=", "")
        replaceLine("dist/xl-converter.desktop", "Exec=", "Exec=AppRun\n")
        
        makedirs(f"dist/AppDir/usr/bin")
        copy("icons/logo.svg", "dist/AppDir")
        shutil.move("dist/xl-converter.desktop", "dist/AppDir/xl-converter.desktop")
        with open("dist/AppDir/AppRun", "w") as f:
            f.write("#!/bin/bash\n\n")
            f.write("exec ${APPDIR}/usr/bin/xl-converter/xl-converter $@")
        addExecPerm(f"dist/AppDir/AppRun")

        shutil.move(f"dist/xl-converter", "dist/AppDir/usr/bin")
        subprocess.run(("misc/appimagetool", "dist/AppDir", f"dist/xl-converter-{VERSION}-x86_64.AppImage"))

    # Pack 7z
    if args.getArg("pack"):
        dst_direct = f"xl-converter-linux-{VERSION}-x86_64"
        dst = f"dist/{dst_direct}"
        makedirs(dst)
        shutil.move("dist/xl-converter", dst)
        shutil.move("dist/install.sh", dst)
        shutil.move("dist/xl-converter.desktop", dst)
        subprocess.run(("7z", "a", f"{dst_direct}.7z", dst_direct), cwd="dist")

    # Log Last Build Platform
    with open("build/last_built_on","w") as last_built_on:
        last_built_on.write(f"{platform.system()}_{platform.architecture()}")

    print(f"[Building] Finished (built to dist/xl-converter)")