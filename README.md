<p align="center">
    <img src="icons/logo.svg" width="20%">
</p>
<h3 align="center">XL Converter</h3>

Powerful image converter for the latest formats with support for multithreading, drag 'n drop, and downscaling.

Available for Windows and Linux.

![](misc/screenshots/screenshot_0.png)

The [documentation](https://xl-docs.codepoems.eu)

## Supported Formats

Encode to **JPEG XL, AVIF, WEBP, and JPG**. Convert from **HEIF** and [more](https://xl-docs.codepoems.eu/supported-formats)

## Features
#### Out of the Box

Just drop your images and convert. XL Converter works out of the box with no setup or steep learning curve. It prioritizes user experience while granting access to cutting-edge technology.

#### JPG Reconstruction

Losslessly transcode JPG to JPEG XL, reverse the process when needed.

#### Multithreading

Use as many CPU cores as you want.

#### Image Proxy

Avoid picky encoders. A proxy is generated when an encoder doesn't support a specific format.

For example, this enables HEIF -> JPEG XL conversion.

#### Downscaling

Scale down images to resolution, percent, shortest (and longest) side, or file size.

#### Smallest Lossless

Utilize multiple formats to achieve the smallest size.

#### Intelligent Effort

Optimize `Effort` for smaller sizes.

#### Metadata

Easily copy and wipe metadata using encoder parameters or ExifTool.

#### JPEGLI

Encode to regular JPG using the highest quality encoder available.

## Bug Reports

You can submit a bug report in 2 ways
- \[public\] Submit a new [GitHub Issue](https://github.com/JacobDev1/xl-converter/issues)
- \[private\] Email me at contact@codepoems.eu

## Contributions

Pull requests are ignored to avoid licensing issues when reusing the code.

Feel free to make bug reports as contributions.

## Building from Source

### Windows 10

Prerequisites:
- Python `3.11.6` (with `pip`)
- `git`

Clone the repo.

```cmd
git clone -b stable --depth 1 https://github.com/JacobDev1/xl-converter.git
cd xl-converter
```

[Provide tool binaries](#providing-tool-binaries).

Setup `venv`.

```cmd
python -m venv env
env\Scripts\activate.bat
pip install -r requirements.txt
```

Install [redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

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

Clone and set up the repo.

```bash
git clone -b stable --depth 1 https://github.com/JacobDev1/xl-converter.git
chmod -R +x xl-converter
cd xl-converter
```

[Provide tool binaries](#providing-tool-binaries).

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
- `make build-7z` - package to a 7z file (with an installer) (requires `p7zip-full`)
- `make build-appimage` - package as an AppImage (requires `fuse`)

### Providing Tool Binaries

To build XL Converter, you need to provide various binaries. This can be quite challenging.

Binaries needed:
- [libjxl](https://github.com/libjxl/libjxl) 0.10.2
    - cjxl
    - djxl
    - jxlinfo
    - cjpegli
- [libavif](https://github.com/AOMediaCodec/libavif) 1.0.3 (**AVIF_CODEC_AOM**)
    - avifenc
    - avifdec
- [imagemagick](https://imagemagick.org/) 7.1.1-15 Q16-HDRI
    - magick - AppImage for Linux
    - magick.exe - Windows
- [exiftool](https://exiftool.org/) 12.77
    - exiftool.exe - Windows
    - exiftool - standalone Perl build
- [oxipng](https://github.com/shssoichiro/oxipng) 0.8.0

Place them in the following directories:
- `xl-converter\bin\win` for Windows (x86_64) 
- `xl-converter/bin/linux` for Linux (x86_64) 

All binaries are built statically. The version numbers should match. Binaries on Windows have an `.exe` extension.

See the official [XL Converter builds](https://github.com/JacobDev1/xl-converter/releases) for examples.

## Info

### Python Version

The project runs on Python `3.11.6`. It should also work on a slightly older version. `3.12` and newer are not supported.

### Large Files

Don't forget `--depth 1` when running `git clone`. This repo contains large files.

### Development Branch

The dev branch can be accessed with

```bash
git clone -b unstable --depth 1 https://github.com/JacobDev1/xl-converter.git
```

## Unit Testing

Unit tests are currently being reworked.

### Running

[Setup repo](#building-from-source).

Create a test environment.

```bash
python3 -m venv env_test
source env/bin/activate
pip install -r requirements.txt
pip install -r requirements_test.txt
```

Run tests (Linux)

```bash
make test
```

Run tests (Windows)

```cmd
python test.py
```

### Deprecated

`tests_old.py` is a deprecated, but still accessible test suite.

To run them, put any image with a varying aspect ratio inside a `sample_img` folder in the project's directory.

```bash
python tests_old.py
```