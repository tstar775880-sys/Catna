# 專案需求說明書 (PRD)：貓咪友善植物辨識與自動化照護管家

## 專案概述
打造一個基於 Python 的 LINE Bot 機器人與自動化排程系統。主要功能是協助貓奴在花市或戶外「拍照或輸入名稱」即時比對植物對貓咪是否有毒（標準參考 ASPCA 資料庫），並在購買後提供個人化的「植物澆水時程定時提醒」功能。

## 技術棧建議
- 語言：Python 3.11+
- 資料庫：MySQL (可自託管於 NAS 或雲端)
- 平台接口：LINE Messaging API (LINE Bot)
- 自動化排程：GitHub Actions (Cron Job) 
- 外部 API：Gemini API (gemini-2.5-flash 免費額度) 或 Pl@ntNet API

---

## 核心功能與實作邏輯

### 1. 資料庫設計 (Database Schema)
請建立一個基礎的植物管理表 `my_garden` 與 ASPCA 快取表：
- `scientific_name` (VARCHAR, PK): 植物學名
- `common_name_tw` (VARCHAR): 繁體中文俗名
- `status` (VARCHAR): 毒性狀態 (safe / toxic / unknown)
- `is_monitored` (BOOLEAN): 是否為已購買且監控中的植物
- `watering_cycle_days` (INT): 澆水週期天數 (例如 7 天)
- `last_watered_date` (DATE): 上次澆水日期

### 2. LINE Bot 即時比對系統 (花市實戰功能)
- **文字查詢**：使用者傳送中文或英文植物名，後端先查本地資料庫，若無則透過 AI/網路搜尋比對 ASPCA「Non-Toxic to Cats」清單，回傳「⭕ 安全無毒」或「❌ 有毒避開」。
- **拍照辨識**：使用者傳送植物照片，後端將圖片送至 Gemini API 或 Pl@ntNet API 辨識出「學名」，再拿學名比對 ASPCA 毒性資料，即時回傳判斷結果。

### 3. 早上 7 點澆水自動化推播 (GitHub Actions)
- 設定一個 GitHub Actions 工作流，利用 Cron Job 定時在**每天早上 7 點（台灣時間）**觸發 Python 腳本。
- **腳本邏輯**：
  1. 連線至資料庫，撈取所有 `is_monitored = True` 的植物。
  2. 計算 `(今天日期 - last_watered_date) >= watering_cycle_days`。
  3. 若符合條件，透過 LINE Notify 或 LINE Bot 發送推播通知：「早安！今天該澆水的植物有：[植物名稱]、[植物名稱]，記得澆透喔！」

---

## 請幫我完成以下任務：
1. 設計完整的 MySQL 資料庫建表 SQL 語法。
2. 撰寫 LINE Bot 的後端主程式 (`app.py`)，包含處理文字與圖片訊息的架構。
3. 撰寫用於 GitHub Actions 定時觸發的澆水計算與推播腳本 (`watering_reminder.py`)。
4. 建立 GitHub Actions 的工作流設定檔 (`.github/workflows/reminder.yml`)。
5. 參考 ASPCA
6. 參考 CliniTox