# mlb_predictor.spec

import os
block_cipher = None

# Include all .py and .db files
datas = [(f, '.') for f in os.listdir('.') if f.endswith('.py') or f.endswith('.db')]

a = Analysis(
    ['run_app.py'],  # Entry point
    pathex=['.'],
    binaries=[],
    datas=datas + [('icon.ico', '.')],  # Also include your icon file
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MLBHitPredictor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 👈 Hide console window
    icon='icon.ico'  # 👈 Set your icon here
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MLBHitPredictor'
)
