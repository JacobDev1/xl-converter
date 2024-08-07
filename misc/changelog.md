## 1.0.2 - 2024-08-07

- Added tooltips
- Added an option to copy original when output is larger (#45)
- Added an option to prevent deleting original when output is larger (#45)
- Added logging to file
- Added custom ExifTool arguments
- Added low RAM mode (#49)
- Fixed UTF-8 support in ExifTool (Windows) (#46)
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