FROM ne-navi-base:latest

WORKDIR /app
# backend コンテキスト内の全コードを取り込む
COPY . /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# chat_explorer を import できるように
ENV PYTHONPATH=/app

CMD ["celery", "-A", "shared.celery_app", "worker", "-B", "-l", "info"]
