# 创建目录
New-Item -ItemType Directory -Force -Path "static/vendor/css"
New-Item -ItemType Directory -Force -Path "static/vendor/js"

# 下载CSS文件
curl -o "static/vendor/css/fullcalendar.min.css" "https://cdn.jsdelivr.net/npm/fullcalendar@5.10.0/main.min.css"
curl -o "static/vendor/css/bootstrap.min.css" "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css"

# 下载JS文件
curl -o "static/vendor/js/fullcalendar.min.js" "https://cdn.jsdelivr.net/npm/fullcalendar@5.10.0/main.min.js"
curl -o "static/vendor/js/bootstrap.bundle.min.js" "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"

Write-Host "下载完成"