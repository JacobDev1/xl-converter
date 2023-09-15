# Multiplatform makefile replacement
# I got fed up with trying to get `make` to work on Windows

import platform, os, shutil, glob, subprocess, PyInstaller.__main__

PROGRAM_NAME = "xl-converter"
PROGRAM_FOLDER = os.path.dirname(os.path.realpath(__file__))

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
os.makedirs("dist")
PyInstaller.__main__.run([
    'main.spec'
])

# Copy Dependencies
print("[Building] Copying dependencies")
if platform.system() == "Windows":
    os.makedirs(f"dist/{PROGRAM_NAME}/bin/win/")
    for i in glob.glob("bin/win/*"):
        shutil.copy(i, f"dist/{PROGRAM_NAME}/bin/win/")
elif platform.system() == "Linux":
    os.makedirs(f"dist/{PROGRAM_NAME}/bin/linux/")
    for i in glob.glob("bin/linux/*"):
        shutil.copy(i, f"dist/{PROGRAM_NAME}/bin/linux/")

# Copy Installer
if platform.system() == "Linux":
    print("[Building] Appending an installer")
    shutil.copy("misc/install.sh","dist")
    shutil.copy("misc/xl-converter.desktop","dist")

# Log Last Build Platform
with open("build/last_built_on","w") as last_built_on:
    last_built_on.write(f"{platform.system()}_{platform.architecture()}")

print(f"[Building] Finished (built to {os.path.join(PROGRAM_FOLDER,'dist','xl-converter')})")