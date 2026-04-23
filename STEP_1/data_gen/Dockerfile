FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir psycopg2-binary==2.9.9 faker==24.8.0

COPY generator.py /app/generator.py
CMD ["python", "/app/generator.py"]
