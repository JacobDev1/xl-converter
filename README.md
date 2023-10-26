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

Convert your JPGs to JPEG XL completely losslessly.

### Technical
#### Multithreading

XL Converter can fully utilize your CPU regardless If an encoder does multitreading well.

This speeds up conversion by a lot, especially for JPEG XL.

#### Image Proxy

Avoid picky encoders. A proxy is generated when an encoder doesn't support a format.

For example, this enables HEIF -> JPEG XL conversion.

## Building

The build will be generated to `dist/xl-converter`.

### Windows

Install [Python3](https://www.python.org/downloads/).

Install dependencies

```
pip install -r requirements.txt
```

Build

```
python build.py
```

#### Troubleshooting

Your executable may return `No module named 'requests'`

To solve this, update `requests`.

`pip install requests --upgrade`

Delete the `build` folder.

Try building again.

### Linux

Install `Python3` and `pip`

```bash
sudo apt update
sudo apt install python3
sudo apt install pip
```

Install Qt dev tools.

```bash
sudo apt-get install '^libxcb.*-dev' libx11-xcb-dev libglu1-mesa-dev libxrender-dev libxi-dev libxkbcommon-dev libxkbcommon-x11-dev
```

Add permissions and enter the folder
```bash
chmod -R 755 xl-converter
cd xl-converter
```

Install dependencies
```bash
make setup
```

Build

```bash
make build
```

## Running

Install dependencies from the [Building](#building) section and replace the last step.

- Windows - `python main.py`
- Linux - `make run`

## Development

- `unstable` - all changes are committed here first
- `stable` - current stable release

Contributions are not accepted to avoid legal issues. Forward your code and feature suggestions to [my email](https://codepoems.eu/about/).