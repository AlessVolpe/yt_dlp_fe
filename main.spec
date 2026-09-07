# main.spec
import os
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],  # Critical: tells PyInstaller to resolve 'modules' imports from src/
    binaries=[],
    datas=[
        ('assets', 'assets'),  # Bundles static icons and assets
    ],
    hiddenimports=[
        'modules.bll.format_converter',
        'modules.bll.process_worker',
        'modules.bll.runner',
        'modules.guis.progress_window',
        'modules.guis.user_interface',
        'modules.loggers.log_handler',
        'config.constants',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='yt_dlp_fe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True temporarily if you need console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)