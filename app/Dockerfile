# process/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install  -r requirements.txt

COPY . .

ENV PORT=8080
ENV RAG_SERVICE_URL=https://rag-service-1053292367606.us-central1.run.app/retrieve
EXPOSE $PORT

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]