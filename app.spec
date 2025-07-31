# app.spec

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

block_cipher = None

# ⚠️ Adjust to match your venv location
VENV_SITE_PACKAGES = r"C:\Project_wissen\heat_map_jacobs\heat_map\Lib\site-packages"

# ✅ Include your app and required folders
datas = [
    ('app.py', '.'),                           # Streamlit main script
    ('modules/*.py', 'modules'),               # Your Python logic modules
    ('data/*.xlsx', 'data'),                   # Your Excel input files
    (f"{VENV_SITE_PACKAGES}/prophet", 'prophet'),
    (f"{VENV_SITE_PACKAGES}/holidays", 'holidays'),
    (f"{VENV_SITE_PACKAGES}/importlib_resources", 'importlib_resources'),
]

# ✅ Include metadata for packages used
datas += copy_metadata('streamlit')
datas += copy_metadata('prophet')
datas += copy_metadata('holidays')
datas += copy_metadata('pandas')
datas += copy_metadata('numpy')
datas += copy_metadata('importlib_resources')

# ✅ Hidden imports (required by PyInstaller to resolve dynamic imports)
hidden_imports = (
    collect_submodules('prophet') +
    collect_submodules('holidays') +
    collect_submodules('importlib_resources') +
    [
        'streamlit',
        'pandas',
        'numpy',
        'openpyxl',
        'xlsxwriter',
        'xml.parsers.expat',
        'importlib_resources',
    ]
)

# Optional: include expat.dll manually if needed
binaries = []
expat_dll = Path(VENV_SITE_PACKAGES).parent.parent / "Library/bin/libexpat.dll"
if expat_dll.exists():
    binaries.append((str(expat_dll), 'libexpat.dll'))

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
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
    name='forecast_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False if you don't want terminal
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='forecast_app'
)
