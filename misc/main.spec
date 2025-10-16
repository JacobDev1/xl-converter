# -*- mode: python ; coding: utf-8 -*-
import platform
from data.constants import VERSION

block_cipher = None
target_arch = "universal2" if platform.system() == "Darwin" else None

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='xl-converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
    icon=['./images/logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='xl-converter',
)
if platform.system() == "Darwin":
    app = BUNDLE(
        coll,
        name='XL Converter.app',
        icon='./images/logo.icns',
        bundle_identifier='eu.codepoems.xl-converter',
        version=VERSION,
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleName': 'XL Converter', 
            'CFBundleDisplayName': 'XL Converter',
            'CFBundleIdentifier': 'eu.codepoems.xl-converter',
            'CFBundleExecutable': 'xl-converter',
            'CFBundleVersion': VERSION,
            'CFBundleShortVersionString': VERSION,
            'LSMinimumSystemVersion': '11.0',
            'CFBundlePackageType': 'APPL',
            'NSHighResolutionCapable': True,
        },
    )

