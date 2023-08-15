<p align="center">
    <img src="icons/logo.svg" width="20%">
</p>
<h3 align="center">XL Converter</h3>

Fast and easy to use JPEG XL converter with multithreading, intelligent effort and drag 'n drop support. Available for both Windows and Linux.

![](screenshots/screenshot_0.png)
![](screenshots/screenshot_1.png)
![](screenshots/screenshot_2.png)

## Donations

I'm currently without a job, so I'd appreciete [your donation](https://liberapay.com/CodePoems).

The programming market is difficult to get into and my IT degree doesn't seem to be of any help. Donations will be used to pay for the hosting of my [website](https://codepoems.eu) where I post tutorials and software.

![](screenshots/screenshot_3.png)

## Install

Windows
- Installer is included

Linux
- To Install - unpack it then run `./install.sh`
- To Uninstall - `sudo rm -r /opt/xl-converter`

## How to Open JPEG XL

- Windows - supported by [XnViewMP](https://www.xnview.com/en/) / [ImageGlass](https://imageglass.org/) / [PhotoQt](https://photoqt.org/) / [PicView](https://picview.org/) / [nomacs](https://nomacs.org/windows-10/) / [GIMP](https://www.gimp.org/)
- Linux - [tutorial](https://codepoems.eu/posts/how-to-open-jpeg-xl-images-on-linux/)

## What is "Intelligent Effort"?

It's a feature I came up with that gives you **smaller file sizes** and quite possibly **better quality**. The downside is **longer convertion time**. I wrote an [article](https://codepoems.eu/posts/jpeg-xl-effort-setting-explained) demystifying the effort argument.

## Building

Make sure [Python3](https://www.python.org/downloads/) is installed beforehand.

The build will be generated to `dist/xl-converter`.

### Windows

Install dependencies

```
python install -r requirements.txt
```

Build

```
python build.py
```

### Linux

Install `Python3` and `pip`

```
sudo apt update
sudo apt install python3
sudo apt install pip
```

Install Qt dev tools.

```bash
sudo apt-get install '^libxcb.*-dev' libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev
```

Install dependencies
```bash
make setup
```

Build

```bash
make linux
```

## Running

Install dependencies from the [Building](#building) section and replace the last step.

- Windows - `python main.py`
- Linux - `make run`

## Supported Formats

Encoding and decoding:
- JPEG XL
- AVIF
- WEBP
- JPG

## Development

- `stable` branch is meant for regular use
- `unstable` branch is where all the development happens

The current release is based on
- [libjxl](https://github.com/libjxl/libjxl)
- [libavif](https://github.com/AOMediaCodec/libavif)
- ImageMagick