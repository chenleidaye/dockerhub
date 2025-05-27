FROM python:3.11-slim

RUN apt-get update && apt-get install -y bash cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY interactive.sh /cronctl.sh


RUN chmod +x cronctl.sh

CMD python main.py && /bin/bash
