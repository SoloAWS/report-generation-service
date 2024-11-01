FROM python:3.9-slim

WORKDIR /app

COPY . /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8009

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8009"]