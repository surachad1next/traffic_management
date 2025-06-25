#!/bin/bash

python3 connect_app.py &

# เริ่ม Flask app ผ่าน Gunicorn + Gevent worker
exec gunicorn app:app \
    --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
    --workers 1 \
    --bind 0.0.0.0:${SERVICE_PORT:-5055} \
    --log-level info \
    --access-logfile - \
    --error-logfile -

# ./.traffic &         # รัน .traffic เป็น background
# python3 connect_app.py   # รัน connect_app.py เป็น foreground