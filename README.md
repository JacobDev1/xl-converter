<p align="center">
    <img src="icons/logo.svg" width="20%">
</p>
<h3 align="center">XL Converter</h3>

Powerful image converter for the latest formats with support for multithreading, dynamic downscaling, drag 'n drop, and intelligent features.

Available for both Windows and Linux.

![](screenshots/screenshot_0.png)

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

![](screenshots/screenshot_4.png)

Manual downscaling methods are also available.

#### Lossless (Only If Smaller)

Picks the smallest out of two.

#### Smallest Lossless

Utilize multiple formats to get the smallest file size.

![](screenshots/screenshot_6.png)

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

**Important**: Supports Python up to version `3.11.6`

### Windows 10

Install Python from [here](https://www.python.org/downloads).

Check `Add Python to environment variables` and `pip` as an option feature.

Install dependencies

```
python -m venv env
env\Scripts\activate.bat
pip install -r requirements.txt
```

(optionally) Run.

```
python main.py
```

Build

```
python build.py
```

Every time you run or build, you need to have the `env` activated.

```bash
env\Scripts\activate.bat
```

### Linux (Ubuntu, Mint etc.)

Install Python.

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

Download and setup repo.

```bash
git clone https://github.com/JacobDev1/xl-converter.git
chmod -R 755 xl-converter
cd xl-converter
```

Install dependencies.

```bash
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```

(optionally) Run.

```bash
make run
```

If it doesn't run, install Qt dev tools.

```bash
sudo apt install '^libxcb.*-dev' libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev
```

Build.

```bash
make build
```

Every time you `run` or `build`, you need to have the `env` activated.

```bash
source env/bin/activate
```

## Development

- `unstable` - all changes are committed here first
- `stable` - current stable release

Contributions are not accepted to avoid legal issues. Forward your code and feature suggestions to [my email](https://codepoems.eu/about/).