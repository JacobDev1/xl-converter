<p align="center">
    <img src="icons/logo.svg" width="20%">
</p>
<h3 align="center">XL Converter</h3>

Powerful image converter for the latest formats with support for multithreading, dynamic downscaling, drag 'n drop, and intelligent features.

Available for both Windows and Linux.

![](misc/screenshots/screenshot_0.png)

## Support This Project

- [Patreon](https://patreon.com/codepoems) - get rewards
- [Ko-Fi](https://ko-fi.com/codepoems) - one-time donation
- [Libera](https://liberapay.com/CodePoems/donate)

## Knowledge-base

Hosted [here](https://xl-converter-docs.codepoems.eu)

Easy to digest documentation with tutorials.

## Supported Formats

Encode to **JPEG XL, AVIF, WEBP, and JPG**.

More details in the [documentation](https://xl-converter-docs.codepoems.eu/supported-formats).

## Features
### General
#### Dynamic Downscaling

Shrink your images to fit under a **desired file size**. XL Converter can dynamically **adjust the resolution** for you.

![](misc/screenshots/screenshot_1.png)

Manual downscaling methods are also available.

#### Lossless (Only If Smaller)

Picks the smallest out of two.

#### Smallest Lossless

Utilize multiple formats to get the smallest file size.

![](misc/screenshots/screenshot_2.png)

### JPEG XL

#### Intelligent Effort

Always get smaller file size and quite possibly better quality.

#### JPG Reconstruction

Save space by converting JPG to JPEG XL losslessly. You can always reconstruct the original JPG.

### Technical
#### Multithreading

XL Converter can fully utilize your CPU regardless If an encoder does multitreading well.

This speeds up conversion by a lot, especially for JPEG XL.

#### Image Proxy

Avoid picky encoders. A proxy is generated when an encoder doesn't support a format.

For example, this enables HEIF -> JPEG XL conversion.

## Running and Building

### Windows 10

Install Python `3.11.6` from [here](https://www.python.org/downloads).

Check `Add Python to environment variables` and `pip` as option features.

Download and enter the repo.

```cmd
cd xl-converter
```

Setup `venv`.

```cmd
python -m venv env
env\Scripts\activate.bat
pip install -r requirements.txt
```

Install redistributables

```cmd
misc\VC_redist.x64.exe
```

Run the application

```cmd
python main.py
```

You can also build it.

```cmd
python build.py
```

### Linux (Ubuntu-based)

Install packages.

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
sudo apt install '^libxcb.*-dev' libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev
```

Clone and setup repo.

```bash
git clone https://github.com/JacobDev1/xl-converter.git
chmod -R 755 xl-converter
cd xl-converter
```

Create and activate a virtual environment.

```bash
python3 -m venv env
source env/bin/activate
```

Install Python dependencies

```bash
pip install -r requirements.txt
```

Now, you can run it.

```bash
make run
```

...or build it.

```bash
make build
```

Extra building modes:
- `make build-7z` - package to a 7z file (with an installer)
- `make build-appimage` - package as an AppImage

### Troubleshooting Build Issues

#### Building on Linux

The build may not be generated successfully, because `PyInstaller` sometimes clashes with virtual environments on Linux.

If the executable doesn't launch do the following.

Deactivate the virtual environment.

```bash
deactivate
```

Install packages globally.
```bash
pip install -r requirements.txt
```

Try again.

```bash
make build
```

#### Python Version on Linux

The project runs on Python `3.11.6`. The one in your repo should work, but If it doesn't use `pyenv` to get this one specifically. 

## Development

- `unstable` - all changes are committed here first
- `stable` - current stable release

Contributions are not accepted to avoid legal issues. Forward your code and feature suggestions to [my email](https://codepoems.eu/about/).