FROM python:3.9-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install pyzmq psycopg2-binary
COPY . .
CMD ["python", "app.py"]