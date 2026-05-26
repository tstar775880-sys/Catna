# Project Agent Rules

本檔案是給 Codex、Antigravity 與其他 AI coding agent 使用的專案規則。

## Communication

- 一律使用繁體中文與使用者溝通。
- 不要使用 icon，除非使用者明確要求。
- 不要使用 emoji，除非使用者明確要求。

## Testing

- 臨時測試程式必須使用 `test_*.py` 命名格式。
- 測試完成後必須刪除臨時測試檔。
- `test_*.py` 檔案應視為可刪除的臨時檔；刪除這些檔案不得影響正式程式運行。

## Web Server

- 如果需要啟動 web server，必須先檢查目標 port 是否已被使用。
- 如果目標 port 已被使用，必須依序順延到下一個可用 port。
- 回報給使用者時，必須明確告知實際啟動的 URL 與 port。
