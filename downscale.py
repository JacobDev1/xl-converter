import shutil, os

import task_status
from variables import (
    CJXL_PATH,
    IMAGE_MAGICK_PATH,
    ALLOWED_RESAMPLING,
    ALLOWED_INPUT_IMAGE_MAGICK,
    DOWNSCALE_LOGS
)
from utils import delete
from pathing import getUniqueFilePath
import metadata
from convert import convert, getDecoder

def _downscaleTemplate(src, dst, _args, resample="Default", n=None):
    """For intenal use only."""
    if task_status.wasCanceled():
        return

    args = []
    if resample != "Default" and resample in ALLOWED_RESAMPLING:
        args.append(f"-filter {resample}")  # Needs to come first
    args.extend(_args)

    convert(IMAGE_MAGICK_PATH, src, dst, args, n)

def downscaleByPercent(src, dst, amount=10, resample="Default", n=None):
    _downscaleTemplate(src, dst, [f"-resize {100 - amount}%"], resample, n)

def downscaleToMaxRes(src, dst, max_w, max_h, resample="Default", n=None):
    _downscaleTemplate(src, dst, [f"-resize {max_w}x{max_h}"], resample, n)

def downscaleToShortestSide(src, dst, max_res, resample="Default", n=None):
    _downscaleTemplate(src, dst, [f"-resize \"{max_res}x{max_res}^>\""], resample, n)

def downscaleToLongestSide(src, dst, max_res, resample="Default", n=None):
    _downscaleTemplate(src, dst, [f"-resize \"{max_res}x{max_res}>\""], resample, n)

def _downscaleToMaxFileSize(params):
    """Downscale image to fit under a certain file size."""
    # Prepare data
    amount = params["step"]
    proxy_src = getUniqueFilePath(params["dst_dir"], params["name"], "png", True)
    shutil.copy(params["src"], proxy_src)

    # Int. Effort
    if params["format"] == "JPEG XL" and params["jxl_int_e"]:
        params["args"][1] = "-e 7"

    # Downscale until it's small enough
    while True:
        if task_status.wasCanceled():
            delete(proxy_src)
            delete(params["dst"])
            return False

        # Normal conversion
        convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

        # Failed conversion check (in case of corrupt images)
        if not os.path.isfile(params["dst"]):
            delete(proxy_src)
            return False

        # Cap amount
        if amount >= 99:
            delete(proxy_src)
            return False

        # If bigger - resize
        if (os.path.getsize(params["dst"]) / 1024) > params["max_size"]:
            amount += params["step"]
            if amount > 99:
                amount = 99 # Cap amount
                log("[Error] Cannot downscale to less than 1%", params["n"])
            
            if task_status.wasCanceled():
                delete(proxy_src)
                delete(params["dst"])
                return False

            downscaleByPercent(params["src"], proxy_src, amount, params["resample"], params["n"])

        else:
            # JPEG XL - intelligent effort
            if params["format"] == "JPEG XL" and params["jxl_int_e"]:
                params["args"][1] = "-e 9"
                e9_tmp = getUniqueFilePath(params["dst_dir"], params["name"], "jxl", True)

                convert(params["enc"], proxy_src, e9_tmp, params["args"], params["n"])

                if os.path.getsize(e9_tmp) < os.path.getsize(params["dst"]):
                    delete(params["dst"])
                    os.rename(e9_tmp, params["dst"])
                else:
                    delete(e9_tmp)

            # Clean-up
            delete(proxy_src)
            return True

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

def _downscaleToMaxFileSizeStepAuto(params):
    # Prepare data
    size_samples = []
    proxy_src = getUniqueFilePath(params["dst_dir"], params["name"], "png", True)
    shutil.copy(params["src"], proxy_src)

    # Int. Effort
    if params["format"] == "JPEG XL" and params["jxl_int_e"]:
        params["args"][1] = "-e 7"

    # Regular conversion
    convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

    if os.path.getsize(params["dst"]) < params["max_size"] * 1024:
        delete(proxy_src)
        return True

    if task_status.wasCanceled():   # These are used at various points to abort the process
        delete(proxy_src)
        return False

    # 1st pass
    downscaleByPercent(params["src"], proxy_src, 10, params["resample"], params["n"])
    convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

    if not os.path.isfile(params["dst"]) or task_status.wasCanceled():  # Failed conversion check (in case of corrupt images)
        delete(proxy_src)
        return False
    
    size_samples.append([os.path.getsize(params["dst"]), 90])
    if size_samples[0][0] < params["max_size"] * 1024:                  # These signal success
        delete(proxy_src)
        return True

    if task_status.wasCanceled():
        delete(proxy_src)
        delete(params["dst"])
        return False
    
    # 2nd pass
    downscaleByPercent(params["src"], proxy_src, 20, params["resample"], params["n"])
    convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])
    
    size_samples.append([os.path.getsize(params["dst"]), 80])
    if size_samples[1][0] < params["max_size"]  * 1024:
        delete(proxy_src)
        return True

    if task_status.wasCanceled():
        delete(proxy_src)
        delete(params["dst"])
        return False

    # Use extrapolated data
    amount = _extrapolateScale(size_samples, params["max_size"] * 1024)
    downscaleByPercent(params["src"], proxy_src, 100 - amount, params["resample"], params["n"])
    convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

    # Scale down until size req. is met
    while os.path.getsize(params["dst"]) > params["max_size"]  * 1024:
        amount -= 10
        if amount <= 0:
            delete(proxy_src)
            delete(params["dst"])
            return False
        
        downscaleByPercent(params["src"], proxy_src, 100 - amount, params["resample"], params["n"])
        convert(params["enc"], proxy_src, params["dst"], params["args"], params["n"])

    # JPEG XL - intelligent effort
    if params["format"] == "JPEG XL" and params["jxl_int_e"]:
        params["args"][1] = "-e 9"
        e9_tmp = getUniqueFilePath(params["dst_dir"], params["name"], "jxl", True)

        convert(params["enc"], proxy_src, e9_tmp, params["args"], params["n"])

        if os.path.getsize(e9_tmp) < os.path.getsize(params["dst"]):
            delete(params["dst"])
            os.rename(e9_tmp, params["dst"])
        else:
            delete(e9_tmp)

    # Cleanup
    delete(proxy_src)
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
        case "Max Resolution":
            args.append(f"-resize {params['width']}x{params['height']}")
        case "Shortest Side":
            args.append(f"-resize \"{params['shortest_side']}x{params['shortest_side']}^>\"")
        case "Longest Side":
            args.append(f"-resize \"{params['longest_side']}x{params['longest_side']}>\"")
    
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

            if os.path.getsize(e9_tmp) < os.path.getsize(params["dst"]):
                delete(params["dst"])
                os.rename(e9_tmp, params["dst"])
            else:
                delete(e9_tmp)

        # Clean-up
        delete(downscaled_path)

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
        delete(proxy_path)

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

        Max File Size
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
    
    if params["mode"] == "Max File Size":
        if params["step_fast"]:
            _downscaleToMaxFileSizeStepAuto(params)
        else:
            _downscaleToMaxFileSize(params)
    elif params["mode"] in ("Percent", "Max Resolution", "Shortest Side", "Longest Side"):
        _downscaleManualModes(params)
    else:
        log(f"[Error] Downscaling mode not recognized ({params['mode']})", params["n"])

def log(msg, n = None):
    if not DOWNSCALE_LOGS:
        return

    if n == None:
        print(msg)
    else:
        print(f"[Worker #{n}] {msg}")