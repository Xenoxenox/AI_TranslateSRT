# AI_TranslateSRT

基於 Google Gemini API 的 Windows 圖形化字幕工具。它會把影片或音訊切成片段，呼叫 Gemini 轉錄/翻譯，校正為 SRT，最後輸出字幕與轉錄情況報告。

此 fork 的目前發行版是 `v2.1.2`，包含 GUI 滾動修正、ASMR 日譯中 prompt 守衛修正、場景預設、Vertex AI 相容自訂端點、輸出目錄與 Windows onefile 打包設定。

## 下載

Windows 使用者可到本 fork 的 Release 頁面下載：

https://github.com/Xenoxenox/AI_TranslateSRT/releases/tag/v2.1.2

下載 `Release_windows_v2.1.2.zip` 後解壓，確認同一資料夾內至少有：

- `AI_TranslateSRT.exe`
- `ffmpeg.exe`

直接雙擊 `AI_TranslateSRT.exe` 啟動。

`config.json` 不會被打包進發行檔，因為它會保存介面中的 API Key。首次啟動後由程式在關閉時自行產生，請勿分享這個檔案。

## 從原始碼執行

需要 Python 3.11+、FFmpeg，以及 Gemini API Key。

```powershell
pip install -r requirements.txt
python transcribe_pro_gui_v2_85.py
```

兩個現役 Python 檔案必須放在同一資料夾：

- `transcribe_pro_gui_v2_85.py`：Tkinter GUI 正式入口
- `transcribe_pro_v6.py`：轉錄管線後端，也可獨立 CLI 執行

後端 CLI 範例：

```powershell
python transcribe_pro_v6.py --file video.mp4 --api_key YOUR_KEY --model_name models/gemini-2.5-pro --workers 1 --rpm 3 --report
```

## 主要功能

- 影片/音訊轉 SRT，支援所有 FFmpeg 可處理的格式。
- GUI 操作，支援完整轉錄、局部轉錄、僅摘要、僅合併 SRT。
- Prompt 可調，支援目標語言、單行字數、術語/人名對照表。
- 場景預設與語言下拉選單，包含 ASMR 相關 prompt 預設。
- 支援官方 Google Gemini API，也支援 Vertex AI 相容的自訂中轉端點。
- 可指定輸出目錄；留空時最終 SRT 與報告輸出到來源檔同目錄。
- 轉錄日誌固定寫入程式資料夾下的 `logs/`。
- `temp/` 保留分段音訊、分段 SRT、raw response，方便恢復任務或手動檢查。
- 支援 `workers` 併發與 `rpm` 每分鐘請求數限制。

## 基本流程

1. 選擇來源影片或音訊。
2. 填入 Gemini API Key，或在環境變數中提供。
3. 選擇模型，例如 `models/gemini-2.5-pro` 或 `models/gemini-2.5-flash`。
4. 設定目標語言、單行字數、術語表。
5. 視需要設定分段秒數、輸出目錄、併發數、RPM。
6. 按「開始轉錄」。
7. 完成後檢查最終 SRT、轉錄情況報告與日誌。

若勾選「使用自訂端點」，必須填 Base URL，例如：

```text
https://example.com/api/vertex-ai
```

自訂端點走 Vertex AI 相容模式並使用內聯音訊；未勾選時維持官方 Google Gemini API 的上傳流程。

## 輸出檔案

轉錄完成後通常會得到：

- `[影片名稱].srt`：最終字幕。
- `[影片名稱]_SRT轉錄情況_[時間].txt`：AI 摘要報告。
- `logs/[影片名稱]_日誌_[時間].txt`：完整執行日誌。

`temp/` 內的中間檔不會自動刪除。確認不再需要恢復任務或重跑片段後，可自行清理。

## 重要安全提醒

- `config.json` 會保存 API Key 明文，已加入 `.gitignore`，不要提交或分享。
- Release zip 不應包含 `config.json`。
- 若自行打包，請確認 `AI_TranslateSRT.spec` 沒有把 `config.json` 放進 `datas`。

## 常見問題

**程式打不開或閃退**

確認 `AI_TranslateSRT.exe` 和 `ffmpeg.exe` 在同一資料夾。若防毒軟體攔截，請加入信任清單後重試。

**API 回應空白**

可能是該段沒有對白、API Key 暫時受限、模型限流或服務端異常。可稍後重試、換 Key、降低 RPM，或改用較低階模型。

**字幕品質需要人工檢查嗎**

需要。請至少檢查轉錄情況報告、重試片段、截斷警告，以及最終 SRT 的時間軸。AI 仍可能漏詞、幻覺、翻譯錯誤或時間偏移。

**局部片段想重跑**

刪除 `temp/` 中對應的分段 `.srt` 和 raw response，重新執行時選擇恢復任務；或使用 GUI 的局部轉錄工具產生可手動合併的片段字幕。

## 開發備註

- `project_old/` 是歷史歸檔，不要修改。
- GUI 透過 `multiprocessing.Process` 執行後端，`process_wrapper` 與 `multiprocessing.freeze_support()` 是 PyInstaller onefile 可用的前提。
- GUI 的 `_build_config_object()` 欄位需與後端 argparse 參數同步。
- SRT 校正核心在 `parse_time_v10` 與 `format_srt_from_text_v16`，重構前應先準備真實樣本回歸。
- 詳細 SRT 校正規則見 `detailed_instruction_manual/SRT_correction_rules.md`。

## To-Do

- API Key 保護：GUI 遮罩、設定檔加密。
- 自訂端點支援補強：錯誤訊息、模型命名與不同中轉服務差異。
- 英文介面或語言檔。
- SRT 校正規則改良。
- 長時間無對白片段的處理策略。
