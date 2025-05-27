FROM python:3.10-slim

WORKDIR /app

COPY app.py ./
COPY start.sh ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt \
    && apt update && apt install -y cron \
    && chmod +x start.sh

CMD ["./start.sh"]
