FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN echo "=== Checking requirements.txt ===" && cat requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=app.py
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]