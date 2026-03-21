# PowerShell Script
# 创建目录
mkdir -Force static/vendor/css
mkdir -Force static/vendor/js

# 下载CSS文件
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/fullcalendar@5.10.0/main.min.css" -OutFile "static/vendor/css/fullcalendar.min.css"
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" -OutFile "static/vendor/css/bootstrap.min.css"

# 下载JS文件
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/fullcalendar@5.10.0/main.min.js" -OutFile "static/vendor/js/fullcalendar.min.js"
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" -OutFile "static/vendor/js/bootstrap.bundle.min.js"

Write-Host "下载完成"