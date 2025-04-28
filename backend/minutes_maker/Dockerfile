FROM ne-navi-base:latest
WORKDIR /app

COPY minutes_maker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY minutes_maker/app ./app
COPY minutes_maker/tests ./tests

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]