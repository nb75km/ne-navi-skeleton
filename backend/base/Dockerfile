FROM python:3.12-slim AS ne-navi-base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# ---------------- common layer ----------------
COPY pyproject.toml ./
COPY backend /app/backend
# pyproject に依存を寄せている場合
# RUN pip install --no-cache-dir -e .
# requirements.txt に残っている場合
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# ------------- dev / test tools ---------------
ENV PYTHONPATH=/app/backend
