# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec：AI_TranslateSRT 單檔 onefile 打包
#
# 重要約束：
#   - 不打包 config.json（含明碼 API Key，使用者首次啟動自行填入後由程式於關閉時生成）
#   - 不打包 ffmpeg.exe（隨發布包置於 exe 同目錄，由 get_ffmpeg_path() 在執行期定位）
#   - 入口為 GUI；後端 transcribe_pro_v6 以 import 方式被收集
#   - multiprocessing 子程序依賴 freeze_support()（程式內已呼叫）

from PyInstaller.utils.hooks import collect_all

# google-genai / grpc / protobuf 動態載入，需完整收集資料與二進位
_datas, _binaries, _hiddenimports = [], [], []
for _pkg in ('google.genai', 'google.auth', 'grpc', 'google.protobuf'):
    d, b, h = collect_all(_pkg)
    _datas += d
    _binaries += b
    _hiddenimports += h

_hiddenimports += [
    'transcribe_pro_v6',
    'multiprocessing',
    'tkinter',
    'tkinter.scrolledtext',
]

a = Analysis(
    ['transcribe_pro_gui_v2_85.py'],
    pathex=[],
    binaries=_binaries,
    datas=_datas,
    hiddenimports=_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AI_TranslateSRT_v2.1.2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
