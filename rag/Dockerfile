# retrieve/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE $PORT

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port","8080"]