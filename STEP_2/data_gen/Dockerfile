FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir psycopg2-binary==2.9.9 faker==37.0.0 ulid-py==1.1.0
COPY generator.py /app/generator.py
CMD ["python", "/app/generator.py"]
