# ใช้ Python base image ที่เหมาะกับ production
FROM python:3.10-slim

# ติดตั้ง dependencies พื้นฐาน
RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    python3-pip \
    htop \
    nano \
    && rm -rf /var/lib/apt/lists/*

# ตั้ง working directory
WORKDIR /app

RUN pip install --upgrade pip

# คัดลอก requirements และติดตั้ง Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอก source code และ binary uwsgi (.traffic)
COPY . .

# ให้ permission กับ binary uwsgi
RUN chmod +x .traffic

# COPY start.sh .
RUN chmod +x start.sh

COPY wait-for-it.sh .
RUN chmod +x wait-for-it.sh

# กำหนดคำสั่งเริ่มต้นเมื่อ container เริ่ม
# CMD ["./.traffic"]
# CMD ["python3", "app.py"]
# CMD ["python3", "connect_app.py"]
# CMD ["bash", "-c", "python3 connect_app.py & ./.traffic"]
# CMD ["sh","./start.sh"]
CMD ["sh", "-c", "./wait-for-it.sh mysql:3306 -- ./start.sh"]