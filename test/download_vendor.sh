#!/bin/bash
cd static/vendor

# 下载CSS
wget https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/3.10.2/fullcalendar.min.css -O css/fullcalendar.min.css
wget https://cdnjs.cloudflare.com/ajax/libs/antd/4.24.10/antd.min.css -O css/antd.min.css

# 下载JS
wget https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.1/moment.min.js -O js/moment.min.js
wget https://cdnjs.cloudflare.com/ajax/libs/fullcalendar/3.10.2/fullcalendar.min.js -O js/fullcalendar.min.js

echo "下载完成"