# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案概述

基於 Google Gemini API 的圖形化工具，將影片/音訊轉錄為帶時間軸的 SRT 字幕並翻譯。整個專案只有兩個核心 Python 檔案，**兩者必須位於同一資料夾**，缺一不可。介面與註解語言為繁體中文。

## 執行與開發

```bash
pip install -r requirements.txt        # 唯一依賴：google-genai（FFmpeg 需另外安裝並在 PATH 或同資料夾）
python transcribe_pro_gui_v2_85.py     # 啟動 GUI（正式入口）

# 後端可獨立當 CLI 跑，繞過 GUI（除錯轉錄流程時很有用）：
python transcribe_pro_v6.py --file 影片.mp4 --api_key KEY \
  --model_name models/gemini-2.5-pro --workers 1 --rpm 3 --report
```

- 沒有測試套件、沒有 lint 設定、沒有建置腳本。Windows 發行版是用 PyInstaller 打包成 `.exe`（程式內以 `getattr(sys, 'frozen', False)` 判斷是否為打包環境來決定 `APP_PATH`）。
- 需要真實的 Gemini API Key 與媒體檔案才能端到端測試；無法在無金鑰環境下完整驗證轉錄流程。
- `project_old/` 是歷史版本歸檔，**不要修改**；只動根目錄的兩個現役檔案。

## 架構

雙檔分層：**GUI 前端** 與 **後端任務模組**，後端可被 import 也可獨立 CLI 執行。

### 前端 `transcribe_pro_gui_v2_85.py`
- Tkinter GUI。`import transcribe_pro_v6 as backend_task`。
- **跨程序執行**：GUI 不直接呼叫後端函式，而是把後端任務丟進 `multiprocessing.Process`（透過 `process_wrapper`）執行，日誌經 `multiprocessing.Queue` 回傳並即時顯示。`multiprocessing.freeze_support()` 是 PyInstaller 打包必需。
- **config 物件**：`_build_config_object()` 組出一個 `SimpleNamespace`，欄位與後端 CLI 的 argparse 參數一一對應。改後端 CLI 參數時，這裡要同步。
- 四個任務入口（由 config 旗標選擇，見 `_run_process`）：完整轉錄 `run_transcription_task`、局部轉錄 `run_partial_transcription_task`、僅摘要 `run_summarize_only_task`、僅合併（`run_transcription_task` 內的 `merge_only` 分支）。
- GUI worker 會在 queue flush 後用 `os._exit()` 強制退出，避免 genai/grpc 背景執行緒讓父程序 `join()` 永久等待。
- `config.json` 在程式關閉時自動寫入 `APP_PATH`，**內含介面上的 API Key**（明碼），啟動時自動載入。改動設定欄位時記得呼叫 `_set_settings_changed`。
- GUI 佈局修正已在 `feat/gui-layout-fix` 收斂：主介面內容包進 Canvas 垂直滾動容器，視窗最小尺寸為 820x600，參數區標籤列固定寬度避免截斷，窗口標題同步為 v2.85.1。smoke 證據在孤立分支 `evidence/gui-layout-fix-smoke` 的 `78dc492`，開發提交 `094659c` 帶有對應 Git note。

### 後端 `transcribe_pro_v6.py`
轉錄管線：`split_audio`（FFmpeg 依 `chunk_duration` 切段）→ 各段呼叫 `transcribe_audio`（Gemini API）→ `format_srt_from_text_v16` 解析校正 → `merge_srts` 合併 → 選擇性 `create_transcription_report`（AI 摘要）。

- **SRT 校正是核心複雜度**：`parse_time_v10`（時間碼修復）+ `format_srt_from_text_v16`（逐行容錯解析）。「嚴重修正」次數超過 `correction_threshold`（預設 6）會觸發整段重跑。詳見 `detailed_instruction_manual/SRT_correction_rules.md`。
- **自訂端點**：`--custom_base_url` 使用 Vertex AI 相容中轉端點（`vertexai=True` + `api_version='v1'`）。自訂端點路徑用 `Part.from_bytes` 內聯音訊；未設定時保持官方 Google `files.upload` 流程。
- **輸出分類**：`--output_dir` 控制最終 SRT 與 SRT 轉錄情況報告位置；留空時輸出到來源檔同目錄。日誌固定寫入 `APP_PATH/logs`，temp 仍保存分段音訊/SRT/raw response。
- **併發與限速**：`ThreadPoolExecutor`（`--workers`）+ `MinuteRateLimiter` 滑動視窗 RPM 限速（`--rpm`）。重試用 `sleep_with_full_jitter`（指數退避 + 全抖動），避免多執行緒同時重試打爆 API。
- **自訂例外**：`EmptyResponseError`（API 空回應）與 `SRTContentParseError`（無法解析出字幕塊）皆會觸發內部重試；連續空回應達 `--empty_abort_threshold` 會中止整個任務。
- **恢復機制**：靠 temp 資料夾內與來源檔名、分段長度一致的 `_chunk_xxx.mp3/.srt` 判斷已完成段落，`--resume` 只補缺、`--recreate` 全部重切。

## Prompt 模板系統（改動需謹慎）

`_build_full_prompt()` 用 `str.format` 把使用者在「主要規則」文字框輸入的內容與多個模板組合。佔位符 `{language}`、`{max_chars}`、`{fifth_priority}`、`{sixth_priority}`、`{seventh_priority}`、`{final_instruction}`、`{terms_list}` 缺一不可——少了任何一個或多打一對大括號，`.format()` 會直接拋例外導致無法啟動轉錄。術語對照表（`原文 = 譯名 = 性別`）由 `_build_full_prompt` 注入 `{terms_list}`。

## 慣例

- 檔名帶版本號（如 `_v2_85`、`v6`），檔頭有逐版修改說明的中文 changelog 註解；做重大改動時沿用此風格更新檔頭註解。
- 路徑一律 `os.path.normpath`，並用 `get_safe_path` 避免覆蓋既有檔案。
- 全程強制 UTF-8（`force_utf8_encoding`、日誌 FileHandler 用 utf-8）。
