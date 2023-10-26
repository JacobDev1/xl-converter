# Multiplatform makefile replacement
# I got fed up with trying to get `make` to work on Windows

import platform, os, shutil, glob, subprocess, PyInstaller.__main__
from VARIABLES import VERSION

PROGRAM_NAME = "xl-converter"
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

if __name__ == '__main__':
    # Clean
    if os.path.isdir("dist"):
        shutil.rmtree("dist")

    # Important - cleans up the build folder If moved to a different platform
    if os.path.isdir("build"):  
        if os.path.isfile("build/last_built_on"):
            last_built_on = open("build/last_built_on","r")
            last_platform = last_built_on.read()
            last_built_on.close()
            
            if last_platform == f"{platform.system()}_{platform.architecture()}":
                print("[Building] Platform matches with previously compiled cache")
                pass
            else:
                print("[Building] Platform mismatch - deleting the cache")
                shutil.rmtree("build") 
                shutil.rmtree("__pycache__")
        else:
            print("[Building] \"last_built_on\" not found - deleting the cache")
            shutil.rmtree("build")
            shutil.rmtree("__pycache__")

    # Preapre Directory and Build Binaries
    print("[Building] Generating binaries")
    makedirs("dist")
    PyInstaller.__main__.run([
        'main.spec'
    ])

    # Copy Dependencies
    print("[Building] Copying dependencies")
    if platform.system() == "Windows":
        copyTree("bin/win/", f"dist/{PROGRAM_NAME}/bin/win")
    elif platform.system() == "Linux":
        copyTree("bin/linux/", f"dist/{PROGRAM_NAME}/bin/linux")

    # Append an Installer
    print("[Building] Appending an installer")
    if platform.system() == "Linux":
        copy("misc/install.sh","dist")
        copy("misc/xl-converter.desktop","dist")
    elif platform.system() == "Windows":
        copy("misc/install.iss","dist")

    # Embed the Version Number
    print("[Building] Embedding the version number")
    if platform.system() == "Linux":
        replaceLine(f"{PROGRAM_FOLDER}/dist/install.sh", "VERSION=", f"VERSION=\"{VERSION}\"\n")
    elif platform.system() == "Windows":
        replaceLine(f"{PROGRAM_FOLDER}/dist/install.iss", "#define MyAppVersion", f"#define MyAppVersion \"{VERSION}\"\n")

    # Log Last Build Platform
    with open("build/last_built_on","w") as last_built_on:
        last_built_on.write(f"{platform.system()}_{platform.architecture()}")

    print(f"[Building] Finished (built to dist/{PROGRAM_NAME})")