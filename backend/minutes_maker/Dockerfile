FROM ne-navi-base:latest
WORKDIR /app

# WeasyPrint 周りのライブラリに加え、日本語フォントをインストール
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-pip \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    # 日本語フォント
    fonts-ipafont-gothic \
    fonts-noto-cjk \
  && rm -rf /var/lib/apt/lists/*

COPY minutes_maker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY minutes_maker/app ./app
COPY minutes_maker/tests ./tests

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
