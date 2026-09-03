import os
from pathlib import Path

from PySide6.QtCore import (
    QMutexLocker,
)

import data.task_status as task_status
from data.constants import (
    IMAGE_MAGICK_PATH,
    ALLOWED_RESAMPLING,
    JPEG_ALIASES,
)
from core.utils import clip
from core.pathing import getUniqueTmpFilePath
import core.metadata as metadata
from core.convert import getDecoder, runBinary, cleanUp, getImageRes
from core.exceptions import CancellationException, GenericException, FileException

# ------------------------------------------------------------
#                           Math
# ------------------------------------------------------------

def _linearRegression(x, y):
    """Identical to numpy.polyfit(x, y, 1)."""
    n = len(x)
    mean_x, mean_y = sum(x) / n, sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x)**2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0
    intercept = mean_y - slope * mean_x

    return slope, intercept

def _extrapolateScale(sample_points, desired_size) -> int:
    """
    Returns estimated percentage the image should be scaled to.

    parameters:
        sample_data - [[size_in_bytes, percentage], [size, prcnt]]
        desired_size - desired size in bytes
    """

    x, y = zip(*sample_points)
    slope, intercept = _linearRegression(x, y)

    x_new = desired_size
    y_new = slope * x_new + intercept

    return int(y_new)

# ------------------------------------------------------------
#                           Helper
# ------------------------------------------------------------

def _isDownscalingNeeded(params) -> bool:
    width, height = getImageRes(params["src"])

    if min(width, height) < 1:
        return True

    match params["mode"]:
        case "Resolution":
            if params['width'] != float("inf") and params['height'] != float("inf"):
                return params["width"] < width or params["height"] < height
            elif params['width'] != float("inf"):
                return params["width"] < width
            elif params['height'] != float("inf"):
                return params["height"] < height
            else:
                return True
        case "Shortest Side":
            return params["shortest_side"] < min(width, height)
        case "Longest Side":
            return params["longest_side"] < max(width, height)
        case "Megapixels":
            return int(params["megapixels"] * 1_000_000) < width * height
        case _:
            return True

def _downscaleToPercent(src, dst, amount=90, resample="Default", delete_if_canceled=[]):
    amount = clip(amount, 1, 100)

    args = []
    if resample != "Default" and resample in ALLOWED_RESAMPLING:
        args.append(f"-filter {resample}")  # Needs to come first
    args.extend([f"-resize {amount}%"])

    runBinary(
        IMAGE_MAGICK_PATH,
        args,
        src,
        dst,
        args_after_input=True,
        delete_if_canceled=delete_if_canceled,
    )

def _getFileSize(file_path: str, cleanup_targets: list[str] = []) -> int:
    """Returns file size in bytes. On fail, deletes files in cleanup_targets, and raises OSError."""
    try:
        return os.path.getsize(file_path)
    except OSError as e:
        for file in cleanup_targets:
            try:
                os.remove(file)
            except OSError:
                pass
        raise

def _checkForSuccess(err_id: str, file_to_check: str, cleanup_targets: list[str] = []) -> None:
    """Checks if an output exists. If it doesn't exist, raises an exception and deletes cleanup_targets."""
    if os.path.isfile(file_to_check):
        return

    for file in cleanup_targets:
        try:
            os.remove(file)
        except OSError as err:
            pass
    raise FileException(err_id, "Output not found.")

def _deleteFile(path: str, raising: bool = True, exc_id: str = "NO_ID") -> None:
    """Deletes a file. Raise an exception if deleting failed."""
    try:
        os.remove(path)
    except OSError as err:
        if raising:
            raise FileException(exc_id, err)
    
# ------------------------------------------------------------
#                           Scaling
# ------------------------------------------------------------

def _downscaleToFileSize(params, mutex):
    # Prepare data
    fault_tolerance = 0.1    # 0.1 is 10%
    size_samples = []
    with QMutexLocker(mutex):
        proxy_src = getUniqueTmpFilePath(params["dst_dir"], "png")

    # JPEG XL - intelligent effort
    if params["format"] == "JPEG XL" and params["jxl_int_e"]:
        params["args"][1] = "-e 7"

    # Sample 2 data points (evenly)
    _downscaleToPercent(
        params["src"],
        proxy_src,
        66,
        params["resample"],
        [proxy_src, params["dst"]],
    )
    _checkForSuccess("D0", proxy_src, [params["dst"]])
    runBinary(
        params["enc"],
        params["args"],
        proxy_src,
        params["dst"],
        args_after_input=(params["enc"] == IMAGE_MAGICK_PATH),
        delete_if_canceled=[proxy_src, params["dst"]],
    )
    _checkForSuccess("D1", params["dst"], [proxy_src])

    file_size = _getFileSize(params["dst"], [proxy_src, params["dst"]])
    size_samples.append([file_size, 66])

    _deleteFile(proxy_src, raising=True, exc_id="D28")
    _deleteFile(params["dst"], raising=True, exc_id="D30")

    _downscaleToPercent(
        params["src"],
        proxy_src,
        33,
        params["resample"],
        [proxy_src, params["dst"]],
    )
    _checkForSuccess("D23", proxy_src, [params["dst"]])
    runBinary(
        params["enc"],
        params["args"],
        proxy_src,
        params["dst"],
        args_after_input=(params["enc"] == IMAGE_MAGICK_PATH),
        delete_if_canceled=[proxy_src, params["dst"]],
    )
    _checkForSuccess("D24", params["dst"], [proxy_src])

    file_size = _getFileSize(params["dst"], [proxy_src, params["dst"]])
    size_samples.append([file_size, 33])

    _deleteFile(proxy_src, raising=True, exc_id="D32")
    _deleteFile(params["dst"], raising=True, exc_id="D25")

    # Use gathered data
    extrapolated_scale = _extrapolateScale(size_samples, params["max_size"] * 1024)
    if extrapolated_scale < 1:          # Error
        raise GenericException("D14", f"Extrapolated scale cannot be lower than 1 ({extrapolated_scale})")
    elif extrapolated_scale >= 100:     # Non-downscaled conversion
        if Path(params["src"]).suffix[1:].lower() in ("png", "jpeg", "jpg"):
            runBinary(
                params["enc"],
                params["args"],
                params["src"],
                params["dst"],
                args_after_input=(params["enc"] == IMAGE_MAGICK_PATH),
                delete_if_canceled=[proxy_src, params["dst"]],
            )
            _checkForSuccess("D26", params["dst"], [proxy_src])
        else:
            runBinary(
                IMAGE_MAGICK_PATH,
                [],
                params["src"],
                proxy_src,
                args_after_input=True,
                delete_if_canceled=[proxy_src],
            )
            _checkForSuccess("D5", proxy_src)
            runBinary(
                params["enc"],
                params["args"],
                proxy_src,
                params["dst"],
                args_after_input=(params["enc"] == IMAGE_MAGICK_PATH),
                delete_if_canceled=[proxy_src, params["dst"]],
            )
            _checkForSuccess("D6", params["dst"], [proxy_src])
            _deleteFile(proxy_src, raising=True, exc_id="D22")
    else:
        while True:
            _downscaleToPercent(
                params["src"],
                proxy_src,
                extrapolated_scale,
                params["resample"],
                [proxy_src, params["dst"]],
            )
            _checkForSuccess("D7", proxy_src, [params["dst"]])
            runBinary(
                params["enc"],
                params["args"],
                proxy_src,
                params["dst"],
                args_after_input=(params["enc"] == IMAGE_MAGICK_PATH),
                delete_if_canceled=[proxy_src, params["dst"]],
            )
            _checkForSuccess("D15", params["dst"], [proxy_src])

            threshold = params["max_size"] * 1024 * (1 + fault_tolerance)
            file_size = _getFileSize(params["dst"], [proxy_src, params["dst"]])
            if file_size < threshold:
                break

            if extrapolated_scale == 1:
                break

            extrapolated_scale -= 10
            if extrapolated_scale < 1:
                extrapolated_scale = 1

        # JPEG XL - intelligent effort
        if params["format"] == "JPEG XL" and params["jxl_int_e"]:
            params["args"][1] = "-e 9"
            with QMutexLocker(mutex):
                e9_tmp = getUniqueTmpFilePath(params["dst_dir"], "jxl")

            runBinary(
                params["enc"],
                params["args"],
                proxy_src,
                e9_tmp,
                delete_if_canceled=[proxy_src, e9_tmp, params["dst"]],
            )
            _checkForSuccess("D8", e9_tmp, [proxy_src])

            e7_size = _getFileSize(params["dst"], [proxy_src, e9_tmp, params["dst"]])
            e9_size = _getFileSize(e9_tmp, [proxy_src, e9_tmp, params["dst"]])

            try:
                if e9_size < e7_size:
                    os.remove(params["dst"])
                    os.rename(e9_tmp, params["dst"])
                else:
                    os.remove(e9_tmp)
            except OSError as err:
                cleanUp([params["dst"], e9_tmp, proxy_src])
                raise FileException("D18", err)
            
        # Cleanup
        _deleteFile(proxy_src, raising=True, exc_id="D31")

def _downscaleManualModes(params, mutex):
    """Internal wrapper for all regular downscaling modes."""
    # Set arguments
    args = []
    if params['resample'] != "Default" and params['resample'] in ALLOWED_RESAMPLING:
        args.append(f"-filter {params['resample']}")
    
    match params["mode"]:
        case "Percent":
            args.append(f"-resize {params['percent']}%")

        case "Resolution":
            if params['width'] != float("inf") and params['height'] != float("inf"):
                args.append(f"-resize {params['width']}x{params['height']}>")
            elif params['width'] != float("inf"):
                args.append(f"-resize {params['width']}x>")
            elif params['height'] != float("inf"):
                args.append(f"-resize x{params['height']}>")
            else:
                raise GenericException("D20", "Expected downscaling disabled.")

        case "Shortest Side":
            args.append(f"-resize {params['shortest_side']}x{params['shortest_side']}^>")

        case "Longest Side":
            args.append(f"-resize {params['longest_side']}x{params['longest_side']}>")

        case "Megapixels":
            megapixels = int(params['megapixels'] * 1_000_000)
            args.append(f"-resize {megapixels}@>")
            
        case _:
            raise GenericException("D2", f"Downscaling mode not recognized ({params['mode']})")
    
    # Downscale
    if params["enc"] == IMAGE_MAGICK_PATH:  # We can just add arguments If the encoder is ImageMagick, since it also handles downscaling
        args.extend(params["args"])
        runBinary(
            IMAGE_MAGICK_PATH,
            args,
            params["src"],
            params["dst"],
            args_after_input=True,
            delete_if_canceled=[params["dst"]],
        )
        _checkForSuccess("D9", params["dst"])
    else:
        if (
            not params["jxl_int_e"] and
            Path(params["src"]).suffix[1:].lower() in ("png", *JPEG_ALIASES) and
            not _isDownscalingNeeded(params)
        ):
            runBinary(
                params["enc"],
                params["args"],
                params["src"],
                params["dst"],
                args_after_input=(params["enc"] == IMAGE_MAGICK_PATH),
                delete_if_canceled=[params["dst"]],
            )
            _checkForSuccess("D12", params["dst"])
            return

        # Downscale
        # Proxy was handled before in Worker.py
        with QMutexLocker(mutex):
            downscaled_path = getUniqueTmpFilePath(params["dst_dir"], "png")

        runBinary(
            IMAGE_MAGICK_PATH,
            args,
            params["src"],
            downscaled_path,
            args_after_input=True,
            delete_if_canceled=[downscaled_path],
        )
        _checkForSuccess("D10", downscaled_path)
        
        # Convert
        if params["format"] == "JPEG XL" and params["jxl_int_e"]: 
            params["args"][1] = "-e 7"

        runBinary(
            params["enc"],
            params["args"],
            downscaled_path,
            params["dst"],
            args_after_input=(params["enc"] == IMAGE_MAGICK_PATH),
            delete_if_canceled=[downscaled_path, params["dst"]],
        )
        _checkForSuccess("D11", params["dst"], [downscaled_path])

        # Intelligent Effort
        if params["format"] == "JPEG XL" and params["jxl_int_e"]: 
            params["args"][1] = "-e 9"

            with QMutexLocker(mutex):
                e9_tmp = getUniqueTmpFilePath(params["dst_dir"], "jxl")

            runBinary(
                params["enc"],
                params["args"],
                downscaled_path,
                e9_tmp,
                args_after_input=(params["enc"] == IMAGE_MAGICK_PATH),
                delete_if_canceled=[downscaled_path, e9_tmp, params["dst"]],
            )
            _checkForSuccess("D29", e9_tmp, [downscaled_path, params["dst"]])

            e7_size = _getFileSize(params["dst"], [downscaled_path, e9_tmp, params["dst"]])
            e9_size = _getFileSize(e9_tmp, [downscaled_path, e9_tmp, params["dst"]])

            try:
                if e9_size < e7_size:
                    os.remove(params["dst"])
                    os.rename(e9_tmp, params["dst"])
                else:
                    os.remove(e9_tmp)
            except OSError as err:
                cleanUp([params["dst"], e9_tmp, downscaled_path])
                raise FileException("D3", err)

        # Clean-up
        _deleteFile(downscaled_path, raising=True, exc_id="D4")

# ------------------------------------------------------------
#                           Public
# ------------------------------------------------------------

def decodeAndDownscale(params, ext, metadata_mode, mutex):
    """Decode to PNG with downscaling support."""
    params["enc"] = getDecoder(ext)

    if params["enc"] == IMAGE_MAGICK_PATH:
        params["args"] = metadata.getArgs(params["enc"], metadata_mode)
        downscale(params, mutex)
    else:
        # Generate proxy
        with QMutexLocker(mutex):
            proxy_src = getUniqueTmpFilePath(params["dst_dir"], "png")
        runBinary(
            params["enc"],
            [],
            params["src"],
            proxy_src,
            delete_if_canceled=[proxy_src],
        )
        _checkForSuccess("D27", proxy_src)

        # Downscale
        params["src"] = proxy_src
        params["enc"] = IMAGE_MAGICK_PATH
        params["args"] = metadata.getArgs(params["enc"], metadata_mode)
        downscale(params, mutex)

        # Cleanup
        _deleteFile(proxy_src, raising=True, exc_id="D19")

def downscale(params, mutex):
    """A wrapper for all downscaling methods. Keeps the same aspect ratio.
    
        "mode" - downscaling mode
        "enc" - encoder path
        "jxl_int_e" - An exception to handle intelligent effort
        "src" - source PNG absolute path
        "dst" - destination absolute path
        "dst_dir": - destination directory
        "name" - item name
        "args" - encoder arguments

        File Size
        "step" - takes % (e.g. 10%). Keep between 5% - 20%
        "max_size" - desired size - takes KiB (e.g. 500 KiB)

        Percent
        "percent" - downscale by that amount

        Max Size
        "width" - max width in px
        "height" - max height in px
        
        Misc
        "resample": - resampling method
        "n" - worker number
    """
    if task_status.wasCanceled():
        raise CancellationException()
    
    if params["mode"] == "File Size":
        _downscaleToFileSize(params, mutex)
    else:
        _downscaleManualModes(params, mutex)
