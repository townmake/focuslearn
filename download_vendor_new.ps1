# 确保目录存在
if (-not (Test-Path -Path "static/vendor/css")) {
    New-Item -ItemType Directory -Force -Path "static/vendor/css" | Out-Null
}
if (-not (Test-Path -Path "static/vendor/js")) {
    New-Item -ItemType Directory -Force -Path "static/vendor/js" | Out-Null
}

# 下载 FullCalendar CSS
Write-Host "Downloading FullCalendar CSS..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/fullcalendar@5.10.0/main.min.css" -OutFile "static/vendor/css/fullcalendar.min.css"
Write-Host "Downloaded FullCalendar CSS" -ForegroundColor Green

# 下载 Bootstrap CSS
Write-Host "Downloading Bootstrap CSS..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" -OutFile "static/vendor/css/bootstrap.min.css"
Write-Host "Downloaded Bootstrap CSS" -ForegroundColor Green

# 下载 FullCalendar JS
Write-Host "Downloading FullCalendar JS..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/fullcalendar@5.10.0/main.min.js" -OutFile "static/vendor/js/fullcalendar.min.js"
Write-Host "Downloaded FullCalendar JS" -ForegroundColor Green

# 下载 Bootstrap JS
Write-Host "Downloading Bootstrap JS..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" -OutFile "static/vendor/js/bootstrap.bundle.min.js"
Write-Host "Downloaded Bootstrap JS" -ForegroundColor Green

# 下载 Axios JS
Write-Host "Downloading Axios JS..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/axios@1.1.2/dist/axios.min.js" -OutFile "static/vendor/js/axios.min.js"
Write-Host "Downloaded Axios JS" -ForegroundColor Green

# 下载 Material Icons CSS
Write-Host "Downloading Material Icons CSS..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://fonts.googleapis.com/icon?family=Material+Icons" -OutFile "static/vendor/css/material-icons.css"
Write-Host "Downloaded Material Icons CSS" -ForegroundColor Green

# 创建字体目录
if (-not (Test-Path -Path "static/vendor/fonts/material-icons")) {
    New-Item -ItemType Directory -Force -Path "static/vendor/fonts/material-icons" | Out-Null
}

# 下载 Material Icons 字体
Write-Host "Downloading Material Icons Font..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://fonts.gstatic.com/s/materialicons/v140/flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2" -OutFile "static/vendor/fonts/material-icons/MaterialIcons-Regular.woff2"
Write-Host "Downloaded Material Icons Font" -ForegroundColor Green

Write-Host "All resources downloaded successfully!" -ForegroundColor Green