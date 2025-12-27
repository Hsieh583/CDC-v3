# CDC-PR 部署指南

## 快速部署

### 環境需求

- Python 3.8+
- pip (Python 套件管理器)
- 可選：SharePoint 存取權限

### 安裝步驟

1. **Clone 專案**
```bash
git clone https://github.com/Hsieh583/CDC-v3.git
cd CDC-v3
```

2. **安裝相依套件**
```bash
pip install -r requirements.txt
```

3. **設定環境變數**
```bash
cp .env.example .env
# 編輯 .env 檔案，至少設定 SECRET_KEY
```

4. **啟動應用**
```bash
python run.py
```

應用將在 `http://localhost:5000` 啟動。

## 前端資源說明

### CDN 與本地資源

預設情況下，系統使用 CDN 載入前端資源（Bootstrap、jQuery、Bootstrap Icons）。這在網際網路環境中運作良好，但在某些情況下可能需要本地資源：

- 內部網路環境（無網際網路存取）
- 安全性要求（不允許外部 CDN）
- 需要離線運作

### 選項 1：使用 CDN（預設，推薦）

優點：
- 無需額外設定
- 自動快取和 CDN 加速
- 檔案大小小

缺點：
- 需要網際網路連線
- 可能有安全性考量

### 選項 2：使用本地資源

如果需要在沒有網際網路的環境中運作，請依照以下步驟：

1. **下載前端資源**

```bash
# 建立靜態資源目錄
mkdir -p app/static/vendor/{css,js}

# 下載 Bootstrap CSS
curl -o app/static/vendor/css/bootstrap.min.css https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css

# 下載 Bootstrap Icons
curl -o app/static/vendor/css/bootstrap-icons.css https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css

# 下載 Bootstrap JS
curl -o app/static/vendor/js/bootstrap.bundle.min.js https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js

# 下載 jQuery
curl -o app/static/vendor/js/jquery.min.js https://code.jquery.com/jquery-3.7.0.min.js
```

2. **修改模板**

編輯 `app/templates/base.html`，將 CDN 連結替換為本地路徑：

```html
<!-- 原本的 CDN -->
<!-- <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"> -->

<!-- 改為本地 -->
<link href="{{ url_for('static', filename='vendor/css/bootstrap.min.css') }}" rel="stylesheet">
<link href="{{ url_for('static', filename='vendor/css/bootstrap-icons.css') }}" rel="stylesheet">

<!-- JavaScript 同理 -->
<script src="{{ url_for('static', filename='vendor/js/jquery.min.js') }}"></script>
<script src="{{ url_for('static', filename='vendor/js/bootstrap.bundle.min.js') }}"></script>
```

## 生產環境部署

### 使用 Gunicorn（推薦）

1. **安裝 Gunicorn**
```bash
pip install gunicorn
```

2. **啟動應用**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

參數說明：
- `-w 4`: 4 個 worker 程序
- `-b 0.0.0.0:5000`: 綁定到所有介面的 5000 埠

### 使用 Nginx 反向代理

1. **安裝 Nginx**
```bash
sudo apt-get install nginx
```

2. **設定 Nginx**

建立 `/etc/nginx/sites-available/cdc-pr`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/CDC-v3/app/static;
        expires 30d;
    }
}
```

3. **啟用站台**
```bash
sudo ln -s /etc/nginx/sites-available/cdc-pr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 使用 Systemd 服務

建立 `/etc/systemd/system/cdc-pr.service`：

```ini
[Unit]
Description=CDC-PR Procurement Case Document Center
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/CDC-v3
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app

[Install]
WantedBy=multi-user.target
```

啟動服務：
```bash
sudo systemctl daemon-reload
sudo systemctl start cdc-pr
sudo systemctl enable cdc-pr
```

## SharePoint 整合

### 設定 SharePoint 連線

在 `.env` 檔案中設定：

```env
SHAREPOINT_SITE_URL=https://yourcompany.sharepoint.com/sites/yoursite
SHAREPOINT_USERNAME=your-username@yourcompany.com
SHAREPOINT_PASSWORD=your-password
SHAREPOINT_ROOT_FOLDER=CDC-PR-Cases
```

### 注意事項

- SharePoint 認證需要有效的帳號密碼
- 建議使用應用程式專用密碼（App Password）
- 如果 SharePoint 連線失敗，系統會自動退回到本地儲存
- 本地儲存路徑：`instance/storage/`

## 資料庫

### SQLite（預設）

- 開發環境推薦
- 檔案位置：`instance/cdc_pr.db`
- 無需額外設定

### PostgreSQL（生產環境推薦）

1. **安裝 psycopg2**
```bash
pip install psycopg2-binary
```

2. **設定 DATABASE_URL**
```env
DATABASE_URL=postgresql://user:password@localhost/cdc_pr
```

### MySQL

1. **安裝 pymysql**
```bash
pip install pymysql
```

2. **設定 DATABASE_URL**
```env
DATABASE_URL=mysql+pymysql://user:password@localhost/cdc_pr
```

## 備份與還原

### 備份資料庫（SQLite）

```bash
# 備份資料庫
cp instance/cdc_pr.db instance/cdc_pr.db.backup

# 備份文件
tar -czf storage-backup.tar.gz instance/storage/
```

### 還原資料庫

```bash
# 還原資料庫
cp instance/cdc_pr.db.backup instance/cdc_pr.db

# 還原文件
tar -xzf storage-backup.tar.gz
```

## 監控與日誌

### 日誌設定

在 `config.py` 中加入：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instance/app.log'),
        logging.StreamHandler()
    ]
)
```

### 健康檢查

建立健康檢查端點（已在 API 中）：

```bash
curl http://localhost:5000/api/stats
```

## 安全性建議

1. **變更預設密鑰**
   - 必須在生產環境中設定強密鑰
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **限制檔案上傳大小**
   - 已設定為 100MB（`config.py` 中的 `MAX_CONTENT_LENGTH`）

3. **使用 HTTPS**
   - 生產環境務必使用 SSL/TLS

4. **定期備份**
   - 建議每日備份資料庫和文件

5. **存取控制**
   - 考慮整合企業認證系統（如 AD、LDAP）

## 常見問題

### Q: 前端樣式沒有載入？
A: 檢查是否能存取 CDN，或按照本文件切換到本地資源。

### Q: 無法連線到 SharePoint？
A: 系統會自動退回到本地儲存，檢查 SharePoint 設定是否正確。

### Q: 如何重設資料庫？
A: 刪除 `instance/cdc_pr.db` 並重新啟動應用。

### Q: 支援多語言嗎？
A: 目前為繁體中文，可透過修改模板檔案支援其他語言。

## 技術支援

如有問題，請在 GitHub 建立 Issue：
https://github.com/Hsieh583/CDC-v3/issues
