## TBA

### Added

- Add process priority option.
- Add more resampling algorithms (#129).
- Add PNG Optimization mode (#101).

### Fixed

- Fix performance issues on 128-thread CPUs (#122).
- Clean up temp file if downscaling was canceled.
- Fix Delete Original on virtual drives on Windows (#134).
- Make extension filters in "Add Files" dialog case-insensitive on Linux (#148).

### Changed

- Improve conversion start and cancel times.
- Speed up downscaling (#141).
- Limit AVIF tune scope to color only, leave alpha default.
- Update `libjxl` to `v0.12.0` (#152).
- Update AOM AV1 to `v3.14.1` (#153).
- Update Oxipng, ExifTool, and ImageMagick.

## 1.2.3 - 2025-10-02

### Added

- Add `--debug` CLI option.
- Add processing order option (#114).

### Fixed

- Fix preserving metadata with ExifTool for some TIFF sources.
- Fix GIF to JPEG XL conversion stalling on Windows (#115).
- Fix Flatpak permission check false positive (#110).
- Restore native file dialog on GTK-based desktop environments (Linux).
- Prioritize "Delete Original" when replacing files in source folder (#111).
- Improve temp file cleanup on cancel.
- Fix icon scaling issues on Windows.

### Changed

- Clear "Read-only" file attributes on Windows (#108).

## 1.2.2 - 2025-05-31

### Changed

- Rework preserving file time attributes (#92).
- Lower bundle size of all builds.
- Disable downscaling without a dialog when unsupported.
- Move ExifTool validation before transcoding.
- Improve desktop integration on Linux (#103).
- Improve error messages for Automatic Lossless JPEG Transcoding.
- Add a check for an unsupported metadata mode.
- Update `SVT-AV1-PSY` to `v3.0.2`.

### Fixed

- Fix custom resampling not being applied (#106).

## 1.2.1 - 2025-04-02

### Added

- Add AOM AV1 image quality (IQ) tuning mode (#99).
- Add Page Up and Page Down navigation to file view.
- Publish this program on [Flathub](https://flathub.org/apps/eu.codepoems.xl-converter) (#95).

### Changed

- Reintroduce limited APNG support.
- Update `libaom` to `v3.12.0`.
- Update `libavif`, `oxipng`, ExifTool, ImageMagick, and Qt.
- Notify user when Flatpak permissions are insufficient.
- Change user data location for Flatpak builds.
- Adjust update checker to Flatpak.

### Fixed

- Account for unsupported routine (#93).
- Fix visual bug where a category button was not lit up.
- Fix "Add Files" button behavior inside Flatpak.

## 1.2.0 - 2025-02-14

### Added

- Add a static RAM optimizer (#57).
- Add a dynamic RAM optimizer based on resolution (#57).
- Add support for portable user data (#82).
- Add support for adding images via arguments.

### Changed

- Rework the Exception View.
- Rework the Smallest Lossless mode.
- Disable the metadata options when unavailable.
- Move ExifTool settings to their own category.
- Exclude PNG from "Copy Original When Result is Larger".
- Update SVT-AV1-PSY to `v2.3.0-B`.
- Update ExifTool to `13.16` (Windows).

### Fixed

- Optimize RAM usage of SVT-AV1-PSY (#83).
- Handle read-only files in the Windows installer automatically (#85).
- Fix RAM leak (#86).
- Fix an edge case in "Delete Original" (#81).
- Fix SVT-AV1-PSY crashes (#84).

### Removed

- Remove "JPEG XL - Optimize RAM Usage" option.
- Remove "Disable Exception Popups" option.

## 1.1.1 - 2025-01-06

### Added

- Add AVIF bit depth selector.
- Add classic themes.
- Publish new documentation (rewritten in Sphinx).

### Changed

- Update `libjxl` to `v0.11.1`.
- Update `libaom` to `v3.11.0`.
- Update `SVT-AV1-PSY` to `2.3.0-A`.
- Update Python to `3.13`.
- Update Qt to `6.8`.
- Improve default theme.
- Change save data in exception view.
- Rework fonts.

### Fixed

- Fix error when downscaling to PNG with PNG as input.
- Fix glitching font on Windows.

### Removed

- Remove `fuse` requirement from the Linux installer.
- Remove APNG as allowed input.

## 1.1.0 - 2024-12-09

### Added

- Add "Verify" feature to Lossless JPEG Transcoding.
- Add "Normalize" feature to Lossless JPEG Transcoding.
- Add new AVIF encoder: `SVT-AV1-PSY` (#70).
- Add instant cancellation.
- Release a portable build for Windows.
- Add "Optimize RAM Usage" option to JPEG XL (#57).
- Add downscaling to megapixels (#67).
- Add image type filters to "Add Files" (#58).
- Add options to disable width or height when downscaling to resolution.
- File dialogs now remember their last used directory (#66).
- Add new theme.

### Changed

- Change default file dialog location to the home directory.
- Terminate encoder processes when application is closed during processing.
- Show `stderr` in exceptions for accurate errors.
- Improve estimated time left accuracy.
- Improve path assignment system to prevent rare path conflicts.
- Adjust UI naming, tooltips and defaults.
- Reduce ExifTool calls required for validation.
- Save widget states to disk more often.
- Anchor progress dialog to the main window.
- Replace "Multithreading" modes with "JPEG XL - Optimize RAM Usage".
- Disable drag and drop during conversion.
- Disable ExifTool for all lossless_jpeg operations.
- Hide the JPEG XL lossy modular mode behind a flag.
- Adjust logs verbosity to lower log file size.
- Update ImageMagick to `7.1.1-41`.
- Update `libavif` to `v1.1.1`.
- Update `AOM AV1` to `v3.10.0`.

### Fixed

- Fix opening URLs on KDE Plasma (#54).
- Fix "Copy Original When Result is Larger" when combined with "Replace" (#60).
- Fix wiping logs stopping log files from being generated until log handler is reloaded (Windows).
- Fix estimated time left counting skipped items as completed (#69).

### Deprecated

- Deprecate "Intelligent Effort" and hide it behind a flag.

### Removed

- Remove the requirement to have `vc_redist` installed.
- Remove `pyqtdarktheme` theme module due to being abandoned.
- Remove HEIC/HEIF support due to licensing issues.

## 1.0.2 - 2024-08-07

- Added tooltips
- Added an option to copy original when output is larger (#45)
- Added an option to prevent deleting original when output is larger (#45)
- Added logging to file
- Added custom ExifTool arguments
- Added low RAM mode (#49)
- Fixed UTF-8 support in ExifTool (Windows) (#47)
- Fixed ExifTool handling of JPEG XL (Linux)
- Fixed menu entry disappearing after an update (Linux)
- Fixed UI bug with multiple chroma subsampling options appearing 
- Set Windows installer to always show dir page
- Improved sound handling
- Improved settings tab scaling
- Switched to the system-provided ExifTool on Linux 
- Updated ExifTool on Windows to `12.92`
- Updated `libavif` to `1.1.1`
- Updated `libaom` to `3.9.1`
- Updated OxiPNG to `0.9.2`

## 1.0.1 - 2024-06-18

- Added dedicated options for lossless JPEG recompression
- Added snapping to sliders
- Added an option to play sound when conversion finishes
- Added a disk space check (#28)
- Added HEIF page-number check
- Fixed light theme in exception view (#29)
- Fixed Linux installer bug (#36)
- Adjusted naming to match the official specs
- Adjusted WebP quality range
- Moved JPEG encoder to the settings
- Moved WebP method to the output tab
- Disabled mouse wheel changing widget values
- Deprecated GIF -> PNG conversion

## 1.0.0 - 2024-05-16

- Added UTF-8 support to JPEG XL and JPEGLI (#6)
- Added parallel AVIF encoding (#20)
- Added partial TIFF support (#23)
- Added chroma subsampling options (#18)
- Added simplified lossy mode picker for JPEG XL
- Added custom encoder parameters to settings
- Added WebP method to settings
- Added better time left estimation
- Added redesigned settings
- Added simpler Windows installation
- Added native `jxl` support to JPEGLI
- Added drag scrolling to settings
- Fixed progress dialog shrinking when minimized (#22)
- Fixed download dialog not closing in the update checker
- Fixed arrow key navigation when no items are selected in the input tab
- Removed lossless (only if smaller)
- Updated OxiPNG to `0.9`

## 0.9.9 - 2024-04-15

- Added "Keep Folder Structure" feature (#16)
- Added "JPEGLI - Disable Progressive Scan" setting (#18)
- Fixed "Disable Delete Original on Startup" (#17)
- Fixed Downscaling to Resolution (#19) 
- Fixed Displaying Text in Exception View
- Cleaned up the Output Tab Visually
- Removed Saving and Loading File Lists from Settings

## 0.9.8 - 2024-03-14

- Added new JPG encoder - JPEGLI
- Added `Encoder - Wipe` support to JPEG XL
- Added support for native `jxl` -> `jxl` conversion (JPEG XL)
- Added thread scaling for small amounts of images (JPEG XL)
- Added experimental Effort 10 to settings (JPEG XL)
- Updated JPEG XL (`libjxl`) to v0.10.2 (faster with lower RAM usage)
- Updated ExifTool to 12.77
- Changed default quality for JPG and WEBP from 80 to 90
- Removed Effort limit for GIFs and APNGs (JPEG XL)
- Adjusted and unified fonts across all platforms
- Fixed start menu icon disappearing after update (Linux)

## 0.9.7 - 2024-02-28

- Added JPEG XL lossy mode selection
    - VarDCT - for natural or complex images, like photographs
    - Modular - for images with sharp edges and flat areas, like digital art, screenshots, documents etc.
- Added more navigation to the input tab
    - Shift + Home or End - select items above / below
    - Shift + Up or Down - add item above / below to selection 
- Added more info to debug reports
- Fixed layout alignment when switching tabs
- Fixed visual bug with lossless_if

## 0.9.6 - 2024-01-23

- Added new version of AVIF (faster and better quality)
- Added UTF-8 support for AVIF (#6)
- Added UTF-8 support for saving and loading file list
- Added new exception logging system
- Added robust error handling
- Added helpful links to about tab
- Added detection for incompatible characters
- Fixed bug in time left algorithm
- Fixed ExifTool problems on some Linux distros
- Improved stability
- Improved process handling
- Improved update checker
- Changed quality scale for AVIF
- Removed broken TIFF support
- Removed donate button
- Renamed metadata modes
- Replaced manual file size downscaling with automatic

## 0.9.5 - 2023-12-21

- Added faster file size downscaling based on linear regression
- Added saving and loading file lists
- Added notification on failed conversions
- Added error handling for corrupt images when downscaling
- Added "Disable Delete Original on Startup" to settings
- Added unit tests
- Fixed Skip mode
- Fixed renaming collisions (#5)
- Fixed downscaling to resolution
- Fixed wrong arg. for JPEG XL (#4)
- Fixed outline on item focus
- Fixed Reset to Default behavior
- Fixed GitHub repo language statistics
- Improved Linux installer
- Improved 3rd party licenses
- Improved exception popup handling
- Applied minor UI tweaks
- Reworked the entire project structure

## 0.9.4 - 2024-11-22

- User Interface
    - 10x faster file addition
    - Improved speed of deleting and selecting items
    - Added navigation methods (arrow keys, Home and End)
    - Improved time left accuracy
- Platform Support
    - Bundled Visual C++ Redistributables with Windows installer
    - Introduced AppImage builds for Linux
- Misc
    - Improved and automated building process
    - Migrated to new packages

## 0.9.3 - 2024-10-31

- Added JPG reconstruction data detection
- Added "Reconstruct JPG from JPEG XL" checkbox to PNG format

## 0.9.2 - 2024-10-26

- New
    - Released [Knowledge-base](https://xl-docs.codepoems.eu)
    - Added metadata handling
        - Preserving
        - Wiping
        - 5 modes in total (encoder and ExifTool-based)
    - Added shortcuts - switch tabs with Alt + 1, 2, 3...
    - Added JPE support
    - Added exception popups If any occurred during conversion
        - Added corresponding option to settings
    - Added Intelligent Effort support to manual downscaling
- Fixes
    - Disabled downscaling on "reset to default"
    - Expanded the convert button in input tab  
    - Added icon to notifications
    - Fixed visual bug with labels in the Modify tab
    - Fixed visual bug with progress dialog
    - Dynamic Downscaling
        - Avoided generating proxy when not necessary
        - Fixed intelligent effort
        - Partially fixed hung ups when generating proxies
    - Improved estimated time left accuracy
    - Manual downscaling
        - Linked custom encoders
        - Rewritten it entirely
- Changes
    - Removed "Best Quality" checkbox (you can just set speed to 0 instead)
    - Disabled downscaling on startup
        - Added corresponding option to settings
    - Redesigned how choosing resampling works

## 0.9.1 - 2023-09-30

- Made drag 'n drop work on every tab
- Improved AVIF encoding stability
- Added widget saving system to make them persistent
- Made iterating on the previously renamed files work between conversions
    - e.g. "file (1).jxl" -> "file (2).jxl" instead of "file (1) (1).jxl"
    - Detection and parsing is RegEx-based
- Added item count to the progress dialog
- Added time left to the progress dialog
- Added an update checker
- Added settings
- Added relative path support for custom output
   - A folder of that name will be created in each file's source directory
- Replaced label with a spinbox in thread selector
- Added start menu entry to the Linux installer
- Corrected the quality slider range for JPEG XL
- Improved AboutTab layout
- Added notifications
- Added safety checks to custom output
- Streamlined versioning
- Fixed UI bugs

## 0.9 - 2023-09-15

- New Feature - downscaling to
    - **max file size**
    - percent
    - max resolution
    - shortest side
    - longest side
- New Feature - preserve date & time
- New Feature - JPG reconstruction
    - JPEG XL (lossless)
    - Smallest Lossless
- Format Support - load extensions regardless of letter case
- Format Support - add .ico support
- Format Support - extend support for JPEG aliases
- UI - simplify names
- UI - rudimentary fullscreen support
- Linux - better installer and updater
- Fix - GIF / APNG - Effort limited to 7 to prevent encoder crashes
- Fix - GIF - decoding now does not freeze the program
- Fix - Smallest Lossless - prevent empty conversion
- Misc. - more responsive task canceling

## 0.8 - 2023-09-07

- Performance - Add Burst Mode - use extra threads for small data sets
- Performance - make adding files faster (62,500 files from an HDD load in 27 seconds now)
- Format Support - generate a proxy when encoder doesn't support the input format
- Format Support - add APNG -> JPEG XL
- Smallest Lossless - add format selection
- AVIF - add "Best Quality" options
- Input Tab - add sorting
- Code - completely rebuilt important modules for easier future progress
- Code - file names are now assigned at the end to avoid naming collisions
- Fix bugs

## 0.7 - 2023-08-19

- Add AVIF, WEBP, JPG encoding and decoding
- Add "lossless (only if smaller)" option
- Add "Smallest Lossless" mode
- Fix bugs

## 0.6 - 2023-08-08

First public release
