#!/bin/bash
./.traffic &         # รัน .traffic เป็น background
python3 connect_app.py   # รัน connect_app.py เป็น foreground