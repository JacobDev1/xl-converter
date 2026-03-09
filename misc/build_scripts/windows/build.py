#!/usr/bin/env python3
"""
A build orchestrator for Windows.

Run from a native Win32 shell.
"""

import argparse
import shutil
import tempfile
import sys
import subprocess
from pathlib import Path
import logging
import os
import platform
import stat

PYTHON_PATH = Path().home() / 'AppData' / 'Local' / 'Programs' / 'Python' / 'Python313' / 'python.exe'
INNOSETUP_PATH = Path('C:/Program Files (x86)/Inno Setup 6/ISCC.exe')
SEVENZIP_PATH = Path('C:/Program Files/7-Zip/7z.exe')     # Used by the other build.py
RUN_DIR = Path.cwd()
ENV_DEV = RUN_DIR / 'env_dev'
ENV_BUILD = RUN_DIR / 'env_build'
SUPPORTED_PYTHON_3_MINOR_VER = (12, 13)

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def check_exists(path: Path, what: str) -> None:
    """Raises FileNotFoundError if a file does not exists, does not raise anything if it does."""
    if not path.exists():
        raise FileNotFoundError(f'{what} not found at {path}')

def check_tools(*tools: str) -> None:
    for tool in tools:
        if shutil.which(tool) is None:
            raise Exception(f'{tool} was not found in PATH')

def run(cmd: list[str], cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed\n\t{cmd}\n\tstderr: {e.stderr}")
        raise

def remove_read_only(path: str) -> None:
    """Removes "Read-only" attribute from files and folders recursively."""
    for file_path in Path(path).rglob("*"):
        if file_path.is_file():
            try:
                file_path.chmod(stat.S_IWRITE)
            except Exception as e:
                raise OSError(f"[removeReadOnly] Failed to remove \"Read-only\" attribute. {e}")

def rmtree(path: str | Path) -> None:
    """Wrapper for shutil.rmtree. Handles Read-only attributes."""
    remove_read_only(path)
    shutil.rmtree(path)

def check_msvc_installed() -> None:
    try:
        proc = subprocess.run(
            [
                os.path.expandvars(r'%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe'),
                '-latest',
                '-products', '*',
                '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
                '-property', 'installationPath',
                '-nologo'
            ],
            text=True,
            check=True,
            capture_output=True,
        )
        if not proc.stdout.strip():
            raise Exception('Visual Studio exists but C++ build tools are not installed.')
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        raise Exception('Visual Studio with Windows 10 or 11 SDK and C++ build tools is required.') from e

def check_environ() -> None:
    if platform.system() != "Windows":
        raise Exception("Run this script on Windows.")

    if 'MSYSTEM' in os.environ:
        raise Exception('Run this script from CMD.')

    if any(not os.path.isdir(d) for d in ('core', 'data', 'misc', 'ui')):
        raise Exception('Run this script from project\'s root directory.')

def check_python_version(python_path: Path | str, compatible_minor_ver: tuple[int]) -> None:
    p = subprocess.run(
        [ str(python_path), '--version' ],
        capture_output=True,
        text=True,
        check=True,
    )
    ver = p.stdout.strip().split()[1]
    major, minor, _ = ver.split('.', 2)
    if int(major) != 3 or int(minor) not in compatible_minor_ver:
        supported_py_ver = ', '.join(f'3.{v}' for v in compatible_minor_ver)
        raise Exception(f'Incompatible Python version. Supported versions: {supported_py_ver}')

def create_venv(python_path: Path | str, target: Path | str) -> None:
    run([str(python_path), '-m', 'venv', str(target)])

def pip_install(python_path: Path | str, *requirements_files: Path | str) -> None:
    run([str(python_path), '-m', 'pip', 'install', '--upgrade', 'pip'])
    req_args = []
    for req_file in requirements_files:
        req_args.extend(['-r', str(req_file)])
    run([str(python_path), '-m', 'pip', 'install'] + req_args)

def build_cli(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Windows build orchestrator')
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip tests.'
    )
    parser.add_argument(
        '--force-clean',
        action='store_true',
        help='Delete old environments.'
    )
    parser.add_argument(
        '--python-path',
        default=PYTHON_PATH,
        help="Path to MSVC-built python.exe."
    )
    parser.add_argument(
        '--inno-path',
        default=INNOSETUP_PATH,
        help='Path to Inno Setup compiler (ISCC.exe).'
    )
    return parser.parse_args(argv)

def main() -> None:
    # ArgumentParser
    args = build_cli()

    # Prepare EXEs
    py_exe = Path(args.python_path)
    inno_exe = Path(args.inno_path)

    check_environ()
    check_exists(py_exe, 'Python interpreter')
    check_python_version(py_exe, SUPPORTED_PYTHON_3_MINOR_VER)
    check_exists(inno_exe, 'Inno Setup (ISCC.exe)')
    check_tools('git')
    check_exists(SEVENZIP_PATH, '7zip')
    check_msvc_installed()

    # Clean
    if args.force_clean:
        for d in (ENV_DEV, ENV_BUILD):
            if d.exists():
                rmtree(d)

    # Run tests
    if not args.skip_tests:
        if not ENV_DEV.exists():
            create_venv(py_exe, ENV_DEV)
        dev_py = ENV_DEV / 'Scripts' / 'python.exe'
        pip_install(dev_py, Path('requirements.txt'), Path('requirements_test.txt'))
        run([str(dev_py), str(RUN_DIR / 'test.py')])
        run([str(dev_py), str(RUN_DIR / 'test_convert.py')])

    # Create build environment
    if not ENV_BUILD.exists():
        create_venv(py_exe, ENV_BUILD)
    build_py = ENV_BUILD / 'Scripts' / 'python.exe'
    pip_install(build_py, Path('requirements.txt'))
    if subprocess.run(     # PyInstaller not installed
        [str(build_py), '-m', 'pip', 'show', 'pyinstaller'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        # Build bootloader
        run([
            'cmd', '/c', 'call',
            Path('misc/build_scripts/windows/pyinstaller.cmd')
        ], cwd=RUN_DIR)

    # Build
    with tempfile.TemporaryDirectory() as tmp_dir:
        export_dir = Path(tmp_dir) / 'export'
        export_dir.mkdir()
        dist_dir = RUN_DIR / 'dist'

        # Portable
        run([str(build_py), str(RUN_DIR / 'build.py'), '-b', 'portable'], cwd=RUN_DIR)
        for f in dist_dir.glob('*.7z'):
            shutil.move(str(f), str(export_dir))

        # InnoSetup
        run([str(build_py), str(RUN_DIR / 'build.py'), '-b', 'innosetup', '-u'], cwd=RUN_DIR)
        run([str(inno_exe), 'install.iss'], cwd=dist_dir)
        for f in (dist_dir / 'Output').glob('*.exe'):
            shutil.move(str(f), str(export_dir))
        for f in dist_dir.glob('*.json'):
            shutil.move(str(f), str(export_dir))

        # Move build artifacts
        rmtree(dist_dir)
        dist_dir.mkdir()
        for i in export_dir.iterdir():
            shutil.move(str(i), str(dist_dir))

    logging.info('Build artifacts in ./dist/')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f'{e}\nBuild aborted')
        sys.exit(1)
