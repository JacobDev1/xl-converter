TOOLTIPS = {
    # Output tab
    "duplicates": "What to do when an output image of the same name already exists.",
    "threads": "How many CPU threads to use for conversion.\n\nHigher means faster, but leaves less resources for other processes.",
    "output_src": "Saves images next to their sources.",
    "output_ct": """Saves images to the specified folder. Supported path types:

- Absolute path (e.g. `C:\\Images\\Converted`) - all images will be saved the specified folder.

- Relative path (e.g. `Converted`) - images will be saved to a folder with the specified name next to each source.""",
    "keep_dir_struct": "Preserves folder hierarchy when saving images.",
    "delete_original": "Deletes the input image after conversion.\n\nDoes not execute if conversion fails.",
    "clear_after_conv": "Clear the file list (in the input tab) after conversion.",
    "format": "Which format are you converting to.\n\nHow should the image be processed.",
    "jxl_modular": "Uses Modular instead of VarDCT for lossy encoding.\n\nEnabled - reduces size and increases eligibility in non-photographic images.\n\nDisabled - uses VarDCT.\n\nThis mode is experimental.\n\nCauses discoloration and additional artifacts around the edges.\n\nUse it sparingly.",
    "jxl_png_fallback": "Image will be decoded to PNG if reconstruction data is not found.",
    "jxl_verify": "Validates that a JPEG image can be reconstructed, and its checksum matches the original.\n\nAn exception will be displayed if any problems occur.\n\nEnabling this option is unnecessary because the transcoding is highly reliable.\n\nHowever, it does provide an additional reassurance.\n\nIf \"Normalize\" is enabled, the checksum of the normalized image will be used instead.\n\nImages will take slightly longer to process if enabled.",
    "jxl_normalize_enable": "Allows for transcoding problematic JPEG images.\n\nRewrites image structure without affecting quality or metadata.\n\nDiscards unnecessary information, such as unused quantization tables or arbitrary tail data.\n\nWith this enabled, the checksum of a JPEG image you can reconstruct will change, and its file size will increase.\n\nEquivalent to `jpegtran -copy all -optimize`. Images will take longer to process if enabled.",
    "jxl_normalize_when": """Controls when to perform "Normalize".

On Fail - will normalize only when transcoding fails then retry.

Always - all sources will be normalized.""",
    "lossless": "Enables lossless compression.\n\nPixel data will stay the same.",
    "lossless_jpeg_xl": "Enables lossless compression.\n\nPixel data will stay the same if given bit depth is supported.\n\nIt does not perform Lossless JPEG Transcoding by default.",
    "int_effort": "Prioritizes smaller file size.\n\nAlternates between Effort 7 and 9 based on context.\n\nLossless and Lossy (Modular) - Effort 9\n\nLossy (VarDCT) - smallest out of Effort 7 and 9.",
    "effort": "Higher means better quality and/or smaller file size but slower.\n\nLossy: higher values result in higher quality. File size may end up larger, especially for non-photographic images.\n\nLossless and Lossy Modular: higher values always result in lower file size.\n\n7 - normal speed with a modest file size.\n\n9 - very slow, but the produces lowest file size or better quality.\n\nTip: Use Effort 7 for big images as it features streaming encoding.",
    "effort_jpeg_recomp": "Higher values result in lower file size and slower transcoding.\n\n7 - normal speed with a modest file size.\n\n9 - very slow, but produces the lowest file size.",
    "speed": "Lower is better quality but slower." ,
    "method": "Higher means better quality and/or smaller file size.\n\nLossless: higher values result in lower file size.\n\nLossy: higher value result in lower file size and typically higher quality. The latter can be subjective.\n\nTypical values: 4 - 6",
    "chroma_subsampling_jpeg": "Controls color compression. Lower number means less color information and smaller file size.\n\nDefault - matches the input or 4:4:4\n\n4:4:4 - full color, the highest quality and file size\n\n4:2:2 - less color (small visual difference) and significant space-saving\n\n4:2:0 - colors may appear washed out",
    "chroma_subsampling_aom_av1": "Controls color compression. Lower number means less color information and smaller file size.\n\nDefault - matches the input or 4:4:4\n\n4:4:4 - full color, the highest quality and file size\n\n4:2:2 - less color (small visual difference) and significant space-saving\n\n4:2:0 - colors may appear washed out\n\n4:0:0 - grayscale",
    "chroma_subsampling_svt_av1_psy": "Controls color compression. Lower number means less color information and smaller file size.\n\n4:2:0 - colors may appear overly-compressed\n\n4:2:0 is only recommended where low color fidelity is not a concern.\n\nSVT-AV1 in libavif only supports 4:2:0.",
    "quality_jpeg_xl": "Higher values result in higher quality and higher file size.\n\n90 - visually lossless\n\n80 - high quality and reasonable file size\n\n70 - medium-high quality and small file size\n\n60 - space-saving, noticeable blurriness",
    "quality_avif": "Higher values result in higher quality and higher file size.\n\n90 - visually lossless\n\n80 - high quality and file size\n\n70 - good balance between quality and file size\n\n60 - space-saving",
    "quality_webp": "Higher values result in higher quality and higher file size.\n\n90 - high quality and large file size\n\n80 - reasonable quality and file size\n\n60 - looks fine only from far away",
    "quality_jpeg": "Higher values result in higher quality and higher file size.\n\n95 - high quality and very large file size\n\n90 - reasonably high quality and large file size\n\n80 - reasonable quality and file size\n\n60 - looks fine only from far away",
    "smallest_lossless_png": "Uses OxiPNG.\n\nSupported bit depth: 16",
    "smallest_lossless_webp": "Supported bit depth: 8",
    "smallest_lossless_jpeg_xl": "Supported bit depth: 16",
    "smallest_lossless_max_comp": "Results in a lower file size and slower transcoding.",
    "oxipng_level": "Higher level has better compression, but it's slower.",
    "oxipng_inplace": "Replace the original file with an optimized version.",

    # Modify tab
    "keep_timestamps": """Preserves original date & time file attributes.""",
    "metadata": "Controls how metadata is handled.\n\nEncoder modes are faster and recommended. ExifTool is more thorough but more error-prone.\n\nEncoder - Wipe - wipes metadata. Works well for encoding everything except PNG, where it depends on the input format.\n\nEncoder - Preserve - preserves metadata. Works on common input formats, may not work for less popular ones.\n\nExifTool - Wipe - Deletes all metadata except orientation, and color profile.\n\nExifTool - Preserve - preserves all metadata.\n\nExifTool - Unsafe Wipe - deletes every last bit of metadata, including color profile. It can potentially alter the final image, but is the most effective.\n\nExifTool - Custom - empty. It allows you to specify custom behavior (in the settings).\n\nView and edit ExifTool commands in the settings (Settings -> ExifTool -> ExifTool Arguments).",
    "downscaling": "Scales down the resolution of your image.",
    "downscaling_resolution_width_enabled": "Checked - restricts width to a given amount of pixels.\n\nUnchecked - imposes no restrictions on width. Disables downscaling for this dimension.",
    "downscaling_resolution_height_enabled": "Checked - restricts height to a given amount of pixels.\n\nUnchecked - imposes no restrictions on height. Disables downscaling for this dimension.",
    "downscaling_resolution_width": "Scales down to fit to a given width in pixels.",
    "downscaling_resolution_height": "Scales down to fit to a given height in pixels.",
    "downscaling_file_size": "Scales image to approximated file size in kibibytes.\n\nIt is much slower than other downscaling modes. Its accuracy and reliability varies.\n\nOther methods are recommended instead.",
    "downscaling_sides": "Makes a particular side fit to the specified pixel count.",
    "downscaling_percent": "Scales to the specified percentage of each dimension.\n\nFor example, 50% of 1920 x 1080 will result in 960 x 540.",
    "downscaling_megapixels": "Scales down to megapixel count.\n\nA megapixel is the total pixel count of an image divided by a million.\n\nFormula: (width * height) / 1 000 000\n\nReference (rounded):\n\n- 0.9 MP - 1280 x 720 (HD)\n\n- 2.1 MP - 1920 x 1080 (Full HD)\n\n- 8.3 MP - 3840 x 2160 (4K)\n\n- 33.2 MP - 7680 x 4320 (8K)",
    "modify_tab_resample": "Controls the resampling method used for downscaling.\n\nDefault:\n\n  - Lanczos for images without transparency.\n\n  - Mitchell for colormapped images or images with transparency.",

    # Settings tab
    "disable_delete_startup": "Disables \"delete original\" (output tab) when you launch the application.",
    "disable_downscaling_startup": "Disables \"downscaling\" (modify tab) when you launch the application.",
    "quality_prec_snap": "Enabled - snaps to individual values.\n\nDisabled - snaps to intervals of every 5 points.",
    "sorting": "Disables file list sorting (input tab), has no impact on performance.",
    "play_sound_on_finish": "Plays a sound when conversion finishes.",
    "jxl_auto_lossless_jpeg": "Enabled - \"Lossless JPEG Transcoding\" will be used instead of regular lossless compression when transcoding JPEG to JPEG XL.\n\nThis saves plenty of space but prevents metadata from being wiped.\n\nIt works with the following \"Format / Mode\" entries:\n\n - JPEG XL (with \"Lossless\" enabled).\n\n - Smallest Lossless (JPEG XL).\n\nDisabled - JPEG will be transcoded the same as any other file. That means a huge file size, but metadata can be stripped.",
    "ram_optimizer": "Allows for processing high-resolution images without excessive RAM usage.\n\nOnly applicable to:\n\n- JPEG XL (with certain settings)\n\n- AVIF (SVT-AV1-PSY)\n\nModes:\n\n- Dynamic - medium RAM usage; only slower for big images.\n\n- Static - smallest RAM usage, but slowest.\n\n- Disabled - unpredictable RAM usage, but quickest.",
    "ram_optimizer_rules": "Visit the documentation to learn more...",
    "jxl_lossy_modular": "Shows or hides the JPEG XL Lossy Modular option in the Output tab.\n\nThis mode is experimental.\n\n- Offers lower file size and better eligibility for non-photographic images.\n\n- Causes discoloration and additional artifacts around the edges.\n\nUse it sparingly.",
    "jpeg_encoder": "JPEGLI - the new state of the art in JPEG encoding. Fast and high quality.\n\nlibjpeg - the original JPEG encoder. Well-tested, stable, and great at preserving noise. Use it when JPEGLI cannot transcode a particular image.",
    "progressive_jpegli": "Enabled - generated JPEG images will be compatible with very old devices, but their file size will increase.\n\nDisabled - generated JPEG images will be smaller and load faster.",
    "avif_bit_depth": "Controls bit depth used for encoding AVIF.\n\n- Auto - uses source image bit depth.\n\n- 12 - the highest color fidelity. Can be smaller than 10-bit in certain cases.\n\n- 10 - reduces color banding, and improves fidelity at a cost of increased file size.\n\n- 8 - lowest file size, but does not handle color transitions smoothly.\n\nNote: 12-bit depth is only available in the AOM AV1 encoder.",
    "avif_encoder": "Encoder used for encoding AVIF images.\n\n- AOM AV1 - stable and feature rich. Best for preserving high-quality.\n\n- SVT-AV1-PSY - a fork of SVT-AV1 with perceptual enhancements.\n\nNote: Each encoder interprets quality values differently.",
    "avif_aom_iq_tune": "Uses IQ (image quality) tuning mode instead of SSIM.\n\nIQ is better for photographic or complex images, but worse for simple synthetic images.",
    "keep_if_larger": "Prevents \"Delete Original\" and \"Replace\" options (output tab) from deleting the original image if the result is larger",
    "copy_if_larger": "If the processed image is larger than the original, the result is discarded, and the original is copied instead.\n\nExcluded: Lossless JPEG Transcoding, JPEG Reconstruction, PNG",
    "jxl_effort_10": "Raises Effort limit from 9 to 10. Effort 10 is experimental and very slow.\n\n- Lossy: provides a very small visual improvement.\n\n- Lossless: lowers file size.\n\n- Lossless JPEG Transcoding: has a tendency to increase file size. Not recommended.",
    "resample": """Enables resampling algorithm selection in the Modify tab.

The default lets ImageMagick choose -- using Lanczos for images without transparency and Mitchell for images with transparency.

Changing resampling can worsen the quality. Make sure you know what you are doing.""",
    "jxl_int_effort": "Shows or hides the JPEG XL Intelligent Effort option in the Output tab.\n\nThis functionality picks Effort based on context.\n\nIt aimed at providing lower file size but made only a marginal difference.\n\nThis feature will be removed in the future.",
    "exiftool_args": "Arguments used for handling metadata, correspond to the options is the modify tab.\n\nSupported variables:\n\n$src - source image path.\n\n$dst - destination image path.\n\nRemember to add \"-overwrite_original\" to avoid leftover files.",
    "encoder_args": "Additional arguments for the encoders.\n\nAll arguments must be valid and can not conflict with already used ones. Inspect logs for more details.",
    "processing_order": """Controls the processing order.

Random - random order; more accurate estimated time left.

Sequential - sorted by path; less fragmentation on HDDs; less accurate estimated time left.

Total processing time remains the same.""",
    "process_priority": """Controls the priority of transcoding processes. Lower priority means slower transcoding, but more responsive system.

Normal - system default.

Below Normal - delegates transcoding to the background.

Idle - lowest priority.""",
}
