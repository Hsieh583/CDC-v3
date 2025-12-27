# CDC-PR 請購案件文件中心

CDC-PR (Procurement Case Document Center) 是一個請購案件文件的受控入口系統，提供案件建立、文件管理、狀態追蹤等功能。

## 系統特色

- ✅ **Early Capture**: 案件可在未定稿、未核准狀態下建立
- ✅ **唯一案件編號**: 系統自動產生格式化案件編號（CDC-PR-YYYY-NNNNN）
- ✅ **自動建立資料夾**: 與 SharePoint 整合或使用本地儲存
- ✅ **Excel 範本**: 自動產生請購單 Excel 範本
- ✅ **狀態管理**: 追蹤案件狀態變更歷程（Draft/Submitted/Approved/Rejected/Closed）
- ✅ **文件管理**: 主文件 + 多個附件，格式不限
- ✅ **雙重儲存**: SQL 資料庫（邏輯） + SharePoint/本地儲存（文件）

## 技術架構

- **後端**: Flask 3.0 + SQLAlchemy
- **前端**: 原生 JavaScript + jQuery + Bootstrap 5
- **資料庫**: SQLite (開發) / 可切換至其他 SQL 資料庫
- **文件儲存**: SharePoint (可選) / 本地儲存 (預設)

## 快速開始

### 1. 安裝相依套件

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

複製 `.env.example` 為 `.env` 並修改設定：

```bash
cp .env.example .env
```

基本設定（本地開發）：
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
```

SharePoint 整合（選配）：
```env
SHAREPOINT_SITE_URL=https://your-site.sharepoint.com/sites/your-site
SHAREPOINT_USERNAME=your-username
SHAREPOINT_PASSWORD=your-password
SHAREPOINT_ROOT_FOLDER=CDC-PR-Cases
```

### 3. 啟動應用

```bash
python run.py
```

應用將啟動於 `http://localhost:5000`

## 系統功能

### 案件管理

- **建立案件**: 輸入案件名稱與備註，系統自動產生案件編號並建立資料夾
- **查詢案件**: 支援關鍵字搜尋、狀態篩選、分頁顯示
- **案件詳情**: 查看完整案件資訊、文件清單、狀態歷程

### 文件管理

- **主文件**: 每個案件必須上傳一個主文件（格式不限）
- **附件**: 可上傳多個附件
- **下載範本**: 下載案件專屬的請購單 Excel 範本

### 狀態管理

支援的狀態：
- `Draft` (草稿): 初始狀態
- `Submitted` (已提交): 案件已提交審核
- `Approved` (已核准): 案件已核准
- `Rejected` (已拒絕): 案件被拒絕
- `Closed` (已結案): 案件已結案

所有狀態變更都會記錄在歷程中。

## API 端點

### 案件相關

- `GET /api/cases` - 取得案件清單
- `POST /api/cases` - 建立新案件
- `GET /api/cases/{id}` - 取得案件詳情
- `PUT /api/cases/{id}/status` - 更新案件狀態

### 文件相關

- `POST /api/cases/{id}/documents` - 上傳文件
- `GET /api/cases/{id}/template` - 下載案件 Excel 範本
- `GET /api/template/blank` - 下載空白 Excel 範本

### 統計相關

- `GET /api/stats` - 取得統計資訊

## 資料庫架構

### Cases (案件主索引)
- `id`: 主鍵
- `case_number`: 案件編號（唯一）
- `title`: 案件名稱
- `current_status`: 當前狀態
- `sharepoint_folder_path`: SharePoint 路徑
- `created_at`: 建立時間
- `updated_at`: 更新時間
- `notes`: 備註

### Documents (文件關聯)
- `id`: 主鍵
- `case_id`: 案件 ID
- `doc_type`: 文件類型 (main/attachment)
- `filename`: 檔案名稱
- `sharepoint_path` / `local_path`: 儲存路徑
- `uploaded_at`: 上傳時間

### StatusHistory (狀態歷程)
- `id`: 主鍵
- `case_id`: 案件 ID
- `old_status`: 舊狀態
- `new_status`: 新狀態
- `changed_at`: 變更時間
- `notes`: 變更說明

## 部署說明

### 生產環境設定

1. 修改 `.env` 設定：
```env
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
DATABASE_URL=<production-database-url>
```

2. 使用 WSGI 伺服器（如 Gunicorn）：
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### 資料庫遷移

使用 SQLite 時，資料庫檔案位於 `instance/cdc_pr.db`。

若要切換至其他資料庫（如 PostgreSQL、MySQL），請修改 `DATABASE_URL` 環境變數。

## 設計原則

1. **最小必要功能**: 只做核心的案件與文件管理
2. **低技術門檻**: 使用原生技術，易於維護
3. **Early Capture**: 支援草稿狀態，降低使用阻力
4. **事實記錄**: 系統不做決策，只記錄變更歷程
5. **雙重儲存**: SQL 記錄邏輯，SharePoint/本地儲存文件

## 明確不做的功能

- ❌ ERP 整合 / 會計分錄
- ❌ 複雜的簽核流程或權限矩陣
- ❌ 文件內容解析或 OCR
- ❌ 附件分類或標籤系統

## 授權

MIT License