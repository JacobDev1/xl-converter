<div align="center">
    <img src="icons/logo.svg" width="20%">
<h3 align="center">XL Converter</h3>

Easy-to-use image converter for modern formats. Supports multithreading, drag 'n drop, and downscaling.

Available for Windows and Linux.

![](misc/screenshots/screenshot_0.png)

Read the [Manual](https://xl-docs.codepoems.eu)
</div>

## Supported Formats

Encode to **JPEG XL, AVIF, WebP, and JPEG**. Convert from **HEIF, TIFF,** and [more](https://xl-docs.codepoems.eu/supported-formats)

## Features
#### Out of the Box

Just drop your images and convert. XL Converter works out of the box with no setup or steep learning curve. It prioritizes user experience while granting access to cutting-edge technology.

#### JPEGLI

Generate fully compatible JPEGs with up to [35% better compression ratio](https://opensource.googleblog.com/2024/04/introducing-jpegli-new-jpeg-coding-library.html).

#### JPEG XL and AVIF

Achieve exceptional quality at a modest size with JPEG XL and AVIF.

#### Parallel Encoding

Encode images in parallel to speed up the process. Control how much CPU to use during encoding.

#### Lossless JPEG Recompression

Losslessly transcode JPEG to JPEG XL, and reverse the process when needed.

#### Downscaling

Scale down images to resolution, percent, shortest (and longest) side, or even file size.

## Bug Reports

You can submit a bug report in 2 ways
- \[public\] Submit a new [GitHub Issue](https://github.com/JacobDev1/xl-converter/issues)
- \[private\] Email me at contact@codepoems.eu

### Sharing Files

You can share logs and images with me when making a bug report.

Upload files to a service like [Disroot Lufi](https://upload.disroot.org/) and send me a download link to contact@codepoems.eu

## Contributions

Pull requests are ignored to avoid licensing issues when reusing the code.

Feel free to make bug reports as contributions.

## Building from Source

> [!NOTE]
> The recommended way of using XL Converter is through the [official binary releases](https://codepoems.eu/xl-converter). The building process is time-consuming and tedious.

### Windows 10

Install:
- Python `3.11.9` (with `pip`)
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
sudo apt install git make curl
```

Install [xcb QPA](https://doc.qt.io/qt-6/linux-requirements.html) dependencies.

```bash
sudo apt install '^libxcb.*-dev' libfontconfig1-dev libfreetype6-dev libx11-dev libx11-xcb-dev libxext-dev libxfixes-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev
```

Install [pyenv](https://github.com/pyenv/pyenv) via [Automatic installer](https://github.com/pyenv/pyenv?tab=readme-ov-file#automatic-installer) then [add it to shell](https://github.com/pyenv/pyenv?tab=readme-ov-file#set-up-your-shell-environment-for-pyenv)

Install Python build packages.

```bash
sudo apt install wget build-essential libreadline-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev liblzma-dev
```

Build and setup Python `3.11.9`.

```bash
pyenv install 3.11.9
pyenv global 3.11.9
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
python main.py
```

or build it.

```bash
python build.py
```

### Providing Tool Binaries

To build XL Converter, you need to provide various binaries. This can be quite challenging.

Binaries needed:
- [libjxl](https://github.com/libjxl/libjxl) `0.10.2` ([with this patch on Windows](https://github.com/JacobDev1/libjxl-utf8))
    - cjxl
    - djxl
    - jxlinfo
    - cjpegli
- [libavif](https://github.com/AOMediaCodec/libavif) `1.0.4` (AOM `3.8.2`)
    - avifenc
    - avifdec
- [imagemagick](https://imagemagick.org/) `7.* Q16-HDRI`
    - magick - AppImage for Linux
    - magick.exe - Windows
- [exiftool](https://exiftool.org/) `12.77`
    - exiftool.exe - Windows
    - exiftool - standalone Perl build
- [oxipng](https://github.com/shssoichiro/oxipng) `0.9.0`

Place them in the following directories:
- `xl-converter\bin\win` for Windows (x86_64) 
- `xl-converter/bin/linux` for Linux (x86_64) 

All binaries should be statically linked.

> [!TIP]
> See the official [XL Converter builds](https://github.com/JacobDev1/xl-converter/releases) for examples.

## Info

> [!IMPORTANT]
> This project runs on Python `3.11`. Other versions are not supported.

> [!NOTE]
> Don't forget `--depth 1` when running `git clone` to avoid large files.

## Unit Testing

### Running

[Setup repo](#building-from-source).

Create a test environment.

```bash
python3 -m venv env_test
source env/bin/activate
pip install -r requirements.txt
pip install -r requirements_test.txt
```

Run tests

```cmd
python test.py
```

You can control which tests to run. Learn more with `python test.py --help`.

### Deprecated

`test_old.py` is a deprecated, but still accessible test suite focusing on conversion results.

```bash
python test_old.py
```