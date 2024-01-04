import shutil, os

import data.task_status as task_status
from data.constants import (
    IMAGE_MAGICK_PATH,
    ALLOWED_RESAMPLING,
    DOWNSCALE_LOGS
)
from core.utils import clip
from core.pathing import getUniqueFilePath
import core.metadata as metadata
from core.convert import convert, getDecoder

# ------------------------------------------------------------
#                           Helper
# ------------------------------------------------------------

def _downscaleToPercent(src, dst, amount=90, resample="Default", n=None):
    amount = clip(amount, 1, 100)

    args = []
    if resample != "Default" and resample in ALLOWED_RESAMPLING:
        args.append(f"-filter {resample}")  # Needs to come first
    args.extend([f"-resize {amount}%"])

    convert(IMAGE_MAGICK_PATH, src, dst, args, n)

def log(msg, n = None):
    if not DOWNSCALE_LOGS:
        return

    if n == None:
        print(msg)
    else:
        print(f"[Worker #{n}] {msg}")

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

def cancelCheck(*tmp_files):
    """Checks if the task was canceled and removes temporary files."""
    if task_status.wasCanceled():
        for file in tmp_files:
            try:
                os.remove(file)
            except OSError as err:
                log(f"[Downscaling - cancelCheck()] {err} ({file})")
        return True
    return False

# ------------------------------------------------------------
#                           Scaling
# ------------------------------------------------------------

def _downscaleToMaxFileSize(params):
    """Downscale image to fit under a certain file size."""
    # Prepare data
    amount = 100
    proxy_src = getUniqueFilePath(params["dst_dir"], params["name"], "png", True)
    shutil.copy(params["src"], proxy_src)

    # Int. Effort
    if params["format"] == "JPEG XL" and params["jxl_int_e"]:
        params["args"][1] = "-e 7"

    # Downscale until it's small enough
    while True:
        if cancelCheck(proxy_src, params["dst"]):
            return False

        # Normal conversion
        convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

        # Failed conversion check (in case of corrupt images)
        if not os.path.isfile(params["dst"]):
            os.remove(proxy_src)
            return False

        # If bigger - resize
        try:
            size = os.path.getsize(params["dst"])
        except OSError as err:
            os.remove(proxy_src)
            os.remove(params["dst"])
            return False

        if (size / 1024) > params["max_size"]:
            amount -= params["step"]
            if amount < 1:
                os.remove(proxy_src)
                log("[Error] Cannot downscale to less than 1%", params["n"])
                return False
            
            if cancelCheck(proxy_src, params["dst"]):
                return False

            _downscaleToPercent(params["src"], proxy_src, amount, params["resample"], params["n"])

        else:
            # JPEG XL - intelligent effort
            if params["format"] == "JPEG XL" and params["jxl_int_e"]:
                params["args"][1] = "-e 9"
                e9_tmp = getUniqueFilePath(params["dst_dir"], params["name"], "jxl", True)

                convert(params["enc"], proxy_src, e9_tmp, params["args"], params["n"])

                try:
                    e7_size = os.path.getsize(params["dst"])
                    e9_size = os.path.getsize(e9_tmp)
                except OSError as err:
                    os.remove(proxy_src)
                    os.remove(params["dst"])
                    return False

                if e9_size < e7_size:
                    os.remove(params["dst"])
                    os.rename(e9_tmp, params["dst"])
                else:
                    os.remove(e9_tmp)

            # Clean-up
            os.remove(proxy_src)
            return True

def _downscaleToFileSizeStepAuto(params):
    # Prepare data
    size_samples = []
    proxy_src = getUniqueFilePath(params["dst_dir"], params["name"], "png", True)

    # JPEG XL - intelligent effort
    if params["format"] == "JPEG XL" and params["jxl_int_e"]:
        params["args"][1] = "-e 7"

    # Sample 2 data points (evenly)
    _downscaleToPercent(params["src"], proxy_src, 66, params["resample"], params["n"])
    convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

    try:
        size_samples.append([os.path.getsize(params["dst"]), 66])
    except OSError as err:
        os.remove(proxy_src)
        os.remove(params["dst"])
        return False

    if cancelCheck(proxy_src, params["dst"]):
        return False

    if not os.path.isfile(params["dst"]):  # Failed conversion check (in case of corrupt images)
        try:
            os.remove(proxy_src)
            os.remove(params["dst"])
        except OSError as err:
            log(f"[Downscaling - Failed Conversion Check] {err} ({params['dst']})", params["n"])
        return False

    _downscaleToPercent(params["src"], proxy_src, 33, params["resample"], params["n"])
    convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

    try:
        size_samples.append([os.path.getsize(params["dst"]), 33])
    except OSError as err:
        log(f"[Downscaling] Getting file sizes failed {err} ({params['dst']})", params["n"])
        os.remove(proxy_src)
        os.remove(params["dst"])
        return False

    os.remove(params["dst"])

    if cancelCheck(proxy_src):
        return False

    # Use gathered data
    extrapolated_scale = _extrapolateScale(size_samples, params["max_size"] * 1024)

    if extrapolated_scale < 0:
        try:
            os.remove(proxy_src)
        except OSError as err:
            log(f"[Downscaling - extrapolated_size < 0] Failed to delete tmp file {err} ({proxy_src})", params["n"])
        return False
    elif extrapolated_scale >= 100:
        # Non-downscaled conversion
        convert(params["enc"], params["src"], params["dst"], params["args"], params["n"])
        try:
            os.remove(proxy_src)
        except OSError as err:
            log(f"[Downscaling] Failed to delete tmp file {err} ({proxy_src})", params["n"])
            return False
        return True
    else:
        while True:
            _downscaleToPercent(params["src"], proxy_src, extrapolated_scale, params["resample"], params["n"])
            convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

            extrapolated_scale -= 10
            
            try:
                size = os.path.getsize(params["dst"])
                threshold = params["max_size"] * 1024 * 1.1   # 10% fault tolerance
                if size < threshold:
                    break
            except OSError as err:
                os.remove(proxy_src)
                os.remove(params["dst"])
                return False

            if cancelCheck(proxy_src, params["dst"]):
                return False
        
        # JPEG XL - intelligent effort
        if params["format"] == "JPEG XL" and params["jxl_int_e"]:
            params["args"][1] = "-e 9"
            e9_tmp = getUniqueFilePath(params["dst_dir"], params["name"], "jxl", True)

            convert(params["enc"], proxy_src, e9_tmp, params["args"], params["n"])

            try:
                e7_size = os.path.getsize(params["dst"])
                e9_size = os.path.getsize(e9_tmp)
                if e9_size < e7_size:
                    os.remove(params["dst"])
                    os.rename(e9_tmp, params["dst"])
                else:
                    os.remove(e9_tmp)
            except OSError as err:
                log(f"[Downscaling - Intelligent Effort] {err} ({params['dst']})", params["n"])
                return False
            
        # Cleanup
        try:
            os.remove(proxy_src)
        except OSError as err:
            log(f"[Downscaling - Clean-up] {err} ({proxy_src})", params["n"])
            return False
        return True

def _downscaleManualModes(params):
    """Internal wrapper for all regular downscaling modes."""
    # Set arguments
    args = []
    if params['resample'] != "Default" and params['resample'] in ALLOWED_RESAMPLING:
        args.append(f"-filter {params['resample']}")
    
    match params["mode"]:
        case "Percent":
            args.append(f"-resize {params['percent']}%")
        case "Resolution":
            args.append(f"-resize {params['width']}x{params['height']}")
        case "Shortest Side":
            args.append(f"-resize {params['shortest_side']}x{params['shortest_side']}^>")
        case "Longest Side":
            args.append(f"-resize {params['longest_side']}x{params['longest_side']}>")
    
    # Downscale
    if params["enc"] == IMAGE_MAGICK_PATH:  # We can just add arguments If the encoder is ImageMagick, since it also handles downscaling
        args.extend(params["args"])
        convert(IMAGE_MAGICK_PATH, params["src"], params["dst"], args, params["n"])
    else:
        downscaled_path = getUniqueFilePath(params["dst_dir"], params["name"], "png", True)

        # Downscale
        # Proxy was handled before in Worker.py
        convert(IMAGE_MAGICK_PATH, params["src"], downscaled_path, args, params["n"])
        
        # Convert
        if params["format"] == "JPEG XL" and params["jxl_int_e"]: 
            params["args"][1] == "-e 7"

        convert(params["enc"], downscaled_path, params["dst"], params["args"], params["n"])

        # Intelligent Effort
        if params["format"] == "JPEG XL" and params["jxl_int_e"]: 
            params["args"][1] = "-e 9"

            e9_tmp = getUniqueFilePath(params["dst_dir"], params["name"], "jxl", True)
            convert(params["enc"], downscaled_path, e9_tmp, params["args"], params["n"])

            try:
                e7_size = os.path.getsize(params["dst"])
                e9_size = os.path.getsize(e9_tmp)

                if e9_size < e7_size:
                    os.remove(params["dst"])
                    os.rename(e9_tmp, params["dst"])
                else:
                    os.remove(e9_tmp)

            except OSError as err:
                log(f"[Downscaling - Intelligent Effort] {err} ({params['dst']})", params["n"])
                return False

        # Clean-up
        try:
            os.remove(downscaled_path)
        except OSError as err:
            log(f"[Downscaling - Clean-up] {err} ({downscaled_path})", params["n"])
            return False

# ------------------------------------------------------------
#                           Public
# ------------------------------------------------------------

def decodeAndDownscale(params, ext, metadata_mode):
    """Decode to PNG with downscaling support."""
    params["enc"] = getDecoder(ext)
    params["args"] = metadata.getArgs(params["enc"], metadata_mode)

    if params["enc"] == IMAGE_MAGICK_PATH:
        downscale(params)
    else:
        # Generate proxy
        proxy_path = getUniqueFilePath(params["dst_dir"], params["name"], "png", True)
        convert(params["enc"], params["src"], proxy_path, [], params["n"])

        # Downscale
        params["src"] = proxy_path
        params["enc"] = IMAGE_MAGICK_PATH
        downscale(params)

        # Clean-up
        try:
            os.remove(proxy_path)
        except OSError as err:
            log(f"Failed to delete tmp file ({proxy_path})", params["n"])

def downscale(params):
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
        return False
    
    if params["mode"] == "File Size":
        if params["step_fast"]:
            _downscaleToFileSizeStepAuto(params)
        else:
            _downscaleToMaxFileSize(params)
    elif params["mode"] in ("Percent", "Resolution", "Shortest Side", "Longest Side"):
        _downscaleManualModes(params)
    else:
        log(f"[Error] Downscaling mode not recognized ({params['mode']})", params["n"])