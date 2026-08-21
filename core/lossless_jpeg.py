import os

from data.constants import CJXL_PATH, DJXL_PATH
from core.convert import runBinary, runJPEGtran
from core.utils import b2sum
from core.exceptions import FileException

def transcodeJPEGtoJPEGXL(
    src_path: str,
    dst_path: str,
    effort: int,
    num_threads: int,
) -> (bool, str, str):
    """Losslessly transcodes a JPEG image into a JPEG XL image.

    Args:
    src_path: source file location. Needs a .jpg extension.
    dst_path: output file location. Needs a .jxl extension.
    effort: jxl effort.
    num_threads: how many threads to use for transcoding.

    Returns:
    (success, stdout, stderr) 

    Exceptions:
    None
    """
    if not os.path.isfile(src_path):
        return (False, "", "Source file not found.")
    stdout, stderr = runBinary(
        CJXL_PATH,
        [
            "--lossless_jpeg=1",
            f"-e {effort}",
            f"--num_threads={num_threads}",
        ],
        src_path,
        dst_path,
    )
    success = os.path.isfile(dst_path)
    return (success, stdout, stderr)

def normalizeJPEG(
    src_path: str,
    dst_path: str,
) -> (bool, str, str):
    """Normalizes a JPEG image by performing `jpegtran -copy all -optimize`. It removes potentially problematic data, such as arbitrary tail data or unused quantization tables. 

    Args:
    src_path: source file location. Needs a .jpg extension.
    dst_path: output file location. Needs a .jpg extension.

    Returns:
    (success, stdout, stderr) 

    Exceptions:
    None
    """
    if not os.path.isfile(src_path):
        return (False, "", "Source file not found.")
    stdout, stderr = runJPEGtran(
        [
            "-copy", "all",
            "-optimize",
        ],
        src_path,
        dst_path,
    )
    success = os.path.isfile(dst_path)
    return (success, stdout, stderr)

def verifyJPEGXLReconstructionData(
    src_path: str,
    org_path: str,
    tmp_file_path: str,
    num_threads: int,
) -> (bool, str, str):
    """Verifies the original JPEG image can be reconstructed from a JPEG XL image with a matching checksum.

    Args:
    src_path: source file location. Needs a .jxl extension.
    org_path: path to the original JPEG image. Needs to have a .jpg extension.
    tmp_file_path: output path to a tmp file. Needs to have a .jpg extension. It will be removed.

    Returns:
    (success, stdout, stderr) 

    Exceptions:
    FileException: if deleting a tmp file fails.
    """
    # Generate
    success, stdout, stderr = reconstructJPEGfromJPEGXL(
        src_path,
        tmp_file_path,
        num_threads,
    )   # Already checks if the source exists, no need to do it twice.
    if not success:
        return (False, stdout, stderr)

    # Check for output
    success = os.path.isfile(tmp_file_path)
    if not success:
        return (False, stdout, stderr)

    # Get checksums
    try:
        src_b2sum, target_b2sum = b2sum(org_path), b2sum(tmp_file_path)
    except Exception as e:
        raise FileException("jxl_verify_1", f"Calculating b2sum failed. {e}")
    
    # Remove tmp file
    try:
        os.remove(tmp_file_path)
    except OSError as e:
        raise FileException("jxl_verify_0", f"Failed to remove tmp file. {e}")
    
    # Verify checksums
    if src_b2sum != target_b2sum:
        return (False, "", "Checksum mismatch.")
    
    return (True, stdout, stderr)

def reconstructJPEGfromJPEGXL(
    src_path: str,
    dst_path: str,
    num_threads: int,
    explicit: bool = False,
) -> (bool, str, str):
    """Reconstructs the original JPEG image from a JPEG XL image.

    Args:
    src_path: source file location. Needs a .jxl extension.
    dst_path: output file location. Needs a .jpg extension.
    num_threads: how many threads to use for transcoding.
    explicit: fail if reconstruction data is not present.

    Returns:
    (success, stdout, stderr) 

    Exceptions:
    None
    """
    if not os.path.isfile(src_path):
        return (False, "", "Source file not found.")

    args = [f"--num_threads={num_threads}"]
    if explicit:
        args.append("--reconstruct_jpeg")

    stdout, stderr = runBinary(
        DJXL_PATH,
        args,
        src_path,
        dst_path,
    )
    success = os.path.isfile(dst_path)
    return (success, stdout, stderr)
